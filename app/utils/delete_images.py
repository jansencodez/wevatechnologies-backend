from typing import List
from cloudinary.uploader import destroy as cloudinary_destroy

async def delete_images_from_cloudinary(image_urls: List[str]):
    for image_url in image_urls:
        # Extract the public_id from the URL
        public_id = image_url.split('/')[-1].split('.')[0]  # Assume URL structure like 'https://res.cloudinary.com/.../image.jpg'
        try:
            # Delete the image from Cloudinary
            cloudinary_destroy(public_id)
        except Exception as e:
            # Log or handle error if Cloudinary deletion fails
            print(f"Error deleting image {public_id} from Cloudinary: {str(e)}")
