import os
import logging
import io
from pathlib import Path
from typing import Optional, List, Dict
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials',
    'https://www.googleapis.com/auth/drive.readonly'
]

TOOLS_DIR = Path(__file__).parent
LANGGRAPH_DIR = TOOLS_DIR.parent.parent
CREDENTIALS_FILE = TOOLS_DIR / "credentials.json"
TOKEN_FILE = LANGGRAPH_DIR / "token.json"

class ClassroomTool:
    def __init__(self):
        self.drive_service = None
        self.service = self.authenticate()

    def authenticate(self):
        """Authenticate with Google Classroom API"""
        creds = None

        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_FILE), SCOPES
            )

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

        self.drive_service = build("drive", "v3", credentials=creds)
        return build("classroom", "v1", credentials=creds)


    def list_courses(self, course_state: Optional[str] = None) -> List[Dict]:
        """
        List Google Classroom courses with optional state filtering.
        """
        try:
            courses = []
            page_token = None
            
            while True:
                params = {
                    'pageSize': 100,
                    'pageToken': page_token,
                }
                if course_state:
                    params['courseStates'] = [course_state]
                
                results = self.service.courses().list(**params).execute()
                
                for course in results.get('courses', []):
                    courses.append({
                        "id": course['id'],
                        "name": course['name'],
                        "state": course.get('courseState')
                    })
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            return courses
            
        except Exception as e:
            raise Exception(f"Failed to list courses: {str(e)}")
    
    def get_course(self, course_id: str) -> Dict:
        """
        Get detailed information about a course.
        """
        try:
            course = self.service.courses().get(id=course_id).execute()
            return {
                "id": course['id'],
                "name": course['name'],
                "description": course.get('description', ''),
                "state": course.get('courseState', 'UNKNOWN'),
                "room": course.get('room', ''),
                "section": course.get('section', '')
            }
        except Exception as e:
            raise Exception(f"Failed to get course: {str(e)}")
    
    def list_coursework(self, course_id: str) -> List[Dict]:
        """List coursework (assignments) for a course."""
        results = self.service.courses().courseWork().list(
            courseId=course_id,
            pageSize=100,
            courseWorkStates=["PUBLISHED"]
        ).execute()

        return [{
            "id": work['id'],
            "title": work.get('title', ''),
            "description": work.get('description', ''),
            "state": work.get('state', 'UNKNOWN'),
            "dueDate": work.get('dueDate'),
            "dueTime": work.get('dueTime')
        } for work in results.get('courseWork', [])]
    
    def list_coursework_materials(self, course_id: str) -> List[Dict]:
        """
        List course work materials (resources/PDFs) for a given course.
        Returns materials with their attachments including Drive files.
        """
        materials_list: List[Dict] = []
        try:
            page_token = None
            while True:
                results = self.service.courses().courseWorkMaterials().list(
                    courseId=course_id,
                    pageSize=100,
                    courseWorkMaterialStates=["PUBLISHED", "DRAFT"],
                    pageToken=page_token,
                ).execute()

                for material in results.get('courseWorkMaterial', []):
                    materials_list.append({
                        "id": material['id'],
                        "title": material.get('title', ''),
                        "description": material.get('description', ''),
                        "state": material.get('state', 'UNKNOWN'),
                        "materials": material.get('materials', []),
                        "creationTime": material.get('creationTime'),
                        "updateTime": material.get('updateTime')
                    })

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            return materials_list
        except Exception as e:
            raise Exception(f"Failed to list coursework materials: {str(e)}")
    
    def download_drive_pdf(self, file_id: str) -> Optional[bytes]:
        """
        Download a PDF file from Google Drive.
        """
        try:
            if not self.drive_service:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                self.drive_service = build('drive', 'v3', credentials=creds)
            
            request = self.drive_service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                done = downloader.next_chunk()
            
            file_buffer.seek(0)
            return file_buffer.read()
            
        except Exception as e:
            logging.warning(f"Failed to download Drive file {file_id}: {str(e)}")
            return None
