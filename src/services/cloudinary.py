import os
import cloudinary
import cloudinary.uploader
# from src.conf.config import config
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)


def upload_image(file):
    """
    The upload_image function uploads an image file to Cloudinary and returns the secure URL of the uploaded image.
    
    :param file: The file object of the image to be uploaded
    :return: The secure URL of the uploaded image
    :doc-author: Trelent
    """
    result = cloudinary.uploader.upload(file)
    return result['secure_url']


def transform_image(image_url: str, transformation_params: dict):
    """
    The transform_image function applies transformations to an existing image on Cloudinary and returns the URL of the transformed image.
    
    :param image_url: str: The URL of the image to be transformed
    :param transformation_params: dict: The dictionary of transformation parameters to apply
    :return: The URL of the transformed image
    :doc-author: Trelent
    """
    logger.debug(f"Transforming image: {image_url} with params: {transformation_params}")

    default_params = {
        'width': None,
        'height': None,
        'crop': None,
        'quality': None,
        'format': None,
        'angle': None,
    }

    params = {k: v for k, v in {**default_params, **transformation_params}.items() if v is not None}

    logger.debug(f"Final transformation options: {params}")

    try:
        public_id = image_url.split('/')[-1].split('.')[0]
        response = cloudinary.uploader.explicit(public_id, type="upload", eager=[params])
        transformed_url = response['eager'][0]['secure_url']
        logger.debug(f"Transformed image URL: {transformed_url}")
        return transformed_url
    except Exception as e:
        logger.error(f"Error during image transformation: {e}")
        return image_url
