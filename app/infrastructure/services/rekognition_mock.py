import uuid

class RekognitionMockService:
    async def create_face_liveness_session(self) -> str:
        """Simulate creating a liveness session"""
        return str(uuid.uuid4())
        
    async def search_faces_by_image(self, image_bytes: bytes) -> bool:
        """Simulate face search, return True to indicate success"""
        return True
