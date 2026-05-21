"""Quick diagnostic script for Vertex AI Imagen."""
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_credentials():
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    logger.info("=== CREDENTIAL CHECK ===")
    logger.info("GOOGLE_APPLICATION_CREDENTIALS = %s", creds_path)
    logger.info("File exists: %s", os.path.exists(creds_path))
    
    project_id = os.environ.get("GOOGLE_PROJECT_ID", "")
    location = os.environ.get("GOOGLE_LOCATION", "us-central1")
    logger.info("GOOGLE_PROJECT_ID = %s", project_id)
    logger.info("GOOGLE_LOCATION = %s", location)
    return project_id, location

def test_vertexai_init(project_id, location):
    logger.info("=== VERTEX AI INIT ===")
    try:
        import vertexai
        vertexai.init(project=project_id, location=location)
        logger.info("vertexai.init() OK")
        return True
    except Exception as e:
        logger.error("vertexai.init() FAILED: %s", e)
        return False

def test_imagen_model():
    logger.info("=== IMAGEN MODEL LOAD ===")
    try:
        from vertexai.preview.vision_models import ImageGenerationModel
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        logger.info("Model loaded OK: %s", model)
        return model
    except Exception as e:
        logger.error("Model load FAILED: %s", e)
        return None

def test_generate(model):
    logger.info("=== IMAGE GENERATION TEST ===")
    try:
        response = model.generate_images(
            prompt="A simple red circle on white background",
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_few",
        )
        logger.info("Response: %s", response)
        logger.info("Images count: %d", len(response.images) if response.images else 0)
        if response.images:
            logger.info("Image[0] type: %s", type(response.images[0]))
            logger.info("SUCCESS - Image generated!")
            return True
        else:
            logger.warning("No images returned (possible safety filter)")
            return False
    except Exception as e:
        logger.error("Generation FAILED: %s", e, exc_info=True)
        return False

if __name__ == "__main__":
    project_id, location = test_credentials()
    if not project_id:
        logger.error("No GOOGLE_PROJECT_ID set!")
        sys.exit(1)
    
    if not test_vertexai_init(project_id, location):
        sys.exit(1)
    
    model = test_imagen_model()
    if not model:
        sys.exit(1)
    
    test_generate(model)
