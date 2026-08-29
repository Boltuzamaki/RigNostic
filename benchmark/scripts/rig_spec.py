"""Shared deterministic constants for the synthetic Stage 0 benchmark."""

CONTROLS = (
    "eyeBlink_L",
    "eyeBlink_R",
    "jawOpen",
    "mouthSmile_L",
    "mouthSmile_R",
    "mouthFunnel",
    "browUp_L",
    "browUp_R",
)

FACE_OBJECT = "FaceMesh"
RIG_OBJECT = "FaceRig"


def driver_path(shape_key: str) -> str:
    return f'key_blocks["{shape_key}"].value'
