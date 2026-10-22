"""PyTorch ResNet9 plant-disease classifier wrapper.

Loads the existing trained weights (plant_disease_weights.pth, converted from
the original notebook model `plant-disease-model-complete.pth`) WITHOUT any
retraining. The 38 class labels are taken verbatim from the training notebook
(torchvision ImageFolder alphabetical classes) so predictions stay aligned with
the checkpoint. Only the presentation layer translates labels to Bengali.
"""
import os
import torch
import torch.nn as nn


def ConvBlock(in_channels, out_channels, pool=False):
    layers = [nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
              nn.BatchNorm2d(out_channels),
              nn.ReLU(inplace=True)]
    if pool:
        layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)


class ResNet9(nn.Module):
    def __init__(self, in_channels, num_diseases):
        super().__init__()
        self.conv1 = ConvBlock(in_channels, 64)
        self.conv2 = ConvBlock(64, 128, pool=True)
        self.res1 = nn.Sequential(ConvBlock(128, 128), ConvBlock(128, 128))
        self.conv3 = ConvBlock(128, 256, pool=True)
        self.conv4 = ConvBlock(256, 512, pool=True)
        self.res2 = nn.Sequential(ConvBlock(512, 512), ConvBlock(512, 512))
        self.classifier = nn.Sequential(nn.MaxPool2d(4),
                                        nn.Flatten(),
                                        nn.Linear(512, num_diseases))

    def forward(self, xb):
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        out = self.classifier(out)
        return out


# Exact ImageFolder alphabetical class order used during training (38 classes).
CLASS_LABELS = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
    'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew',
    'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
    'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy',
    'Grape___Black_rot', 'Grape___Esca_(Black_Measles)',
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
    'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
    'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight',
    'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy',
    'Soybean___healthy', 'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch',
    'Strawberry___healthy', 'Tomato___Bacterial_spot', 'Tomato___Early_blight',
    'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy',
]

WEIGHTS_FILE = "plant_disease_weights.pth"

# The API prefers the tracked state-dict checkpoint and may also load the
# tracked original full-model checkpoint as a local fallback. These URLs are
# retained for legacy standalone callers that need to retrieve missing weights.
MODEL_URLS = [
    "https://github.com/NawrizTurjo/Agri-Smart-BD/raw/main/plant_disease_weights.pth",
    "https://github.com/NawrizTurjo/smart-krishi-buddhimotta/raw/main/plant_disease_weights.pth",
]
MODEL_URL = MODEL_URLS[0]
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         ".streamlit", "cache")


def ensure_weights(weights_path=WEIGHTS_FILE):
    """Return a local path to the weights, downloading once if missing."""
    if os.path.exists(weights_path):
        return weights_path
    # also check the cache dir
    cached = os.path.join(CACHE_DIR, os.path.basename(weights_path))
    if os.path.exists(cached):
        return cached
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        import requests as _rq
        last_err = None
        for url in MODEL_URLS:
            try:
                resp = _rq.get(url, timeout=300, stream=True, allow_redirects=True)
                resp.raise_for_status()
                if len(resp.content) < 1_000_00:  # sanity: real file is ~26 MB
                    raise ValueError(f"unexpected small file from {url}")
                tmp = cached + ".part"
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
                os.replace(tmp, cached)
                return cached
            except Exception as e:
                last_err = e
        raise FileNotFoundError(
            f"Trained weights could not be downloaded ({last_err}). Place "
            f"'{weights_path}' next to app.py manually.") from None
    except OSError as e:
        raise FileNotFoundError(f"Weights cache dir error: {e}") from None


def _torch_load(path):
    """Load state dicts and trusted legacy full checkpoints across PyTorch versions."""
    import __main__

    # The bundled original full-model checkpoint was saved in a notebook, so
    # its pickle refers to ``__main__.ResNet9``. Point that name at this
    # project's compatible architecture only for the duration of torch.load.
    missing = object()
    previous_resnet9 = getattr(__main__, "ResNet9", missing)
    __main__.ResNet9 = ResNet9
    try:
        try:
            obj = torch.load(path, map_location="cpu")  # PyTorch <2.6 default (weights_only=False)
            if isinstance(obj, dict) and "state_dict" in obj:
                obj = obj["state_dict"]
            return obj
        except Exception:
            pass
        # PyTorch >=2.6 defaults to weights_only=True; allow our trusted classes.
        try:
            return torch.load(path, map_location="cpu", weights_only=False)
        except Exception:
            return torch.load(path, map_location="cpu", weights_only=True)
    finally:
        if previous_resnet9 is missing:
            delattr(__main__, "ResNet9")
        else:
            __main__.ResNet9 = previous_resnet9


def load_resnet9(weights_path=WEIGHTS_FILE):
    """Load the pretrained ResNet9.

    Accepts either a plain state_dict (plant_disease_weights.pth) or a full
    pickled model object saved by torch.save(model) (the original notebook
    checkpoint plant-disease-model-complete.pth). No retraining involved.
    """
    obj = _torch_load(ensure_weights(weights_path))
    if isinstance(obj, nn.Module):          # full model checkpoint (original style)
        obj.eval()
        return obj
    if hasattr(obj, "model"):               # LightningModule-style wrapper from notebook
        inner = obj.model if isinstance(getattr(obj, "model", None), nn.Module) else None
        if inner is not None:
            inner.eval()
            return inner
    model = ResNet9(3, len(CLASS_LABELS))   # plain state_dict checkpoint
    if isinstance(obj, dict) and "state_dict" in obj:
        obj = obj["state_dict"]
    model.load_state_dict(obj)
    model.eval()
    return model


def predict_torch(model, img_tensor):
    """Run inference on a preprocessed tensor (1,3,H,W). Returns probs array."""
    import numpy as np
    with torch.no_grad():
        logits = model(img_tensor)
        probs = torch.softmax(logits, dim=1)[0].numpy()
    return probs
