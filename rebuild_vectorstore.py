#!/usr/bin/env python3
"""
Script to rebuild the vectorstore by processing all classroom materials.
Run this when you want to reindex your classroom PDFs.
"""
import sys
from pathlib import Path

# Add langgraph src to path
langgraph_src = str(Path(__file__).parent / "langgraph" / "src")
sys.path.insert(0, langgraph_src)

from tools.classroomTools import ClassroomTool
from tools.pdf_processor import PDFProcessor

def rebuild_vectorstore():
    """Fetch all courses and materials, then index PDFs."""
    print("Starting vectorstore rebuild...")
    
    classroom_tools = ClassroomTool()
    pdf_processor = PDFProcessor(classroom_tools)
    
    # Get all courses
    courses = classroom_tools.list_courses()
    print(f"Found {len(courses)} courses")
    
    total_stats = {"materials_processed": 0, "pdfs_found": 0, "chunks_indexed": 0}
    
    for course in courses:
        try:
            print(f"\nProcessing {course['name']} ({course['id']})...")
            
            # Get course materials
            materials = classroom_tools.list_coursework_materials(course['id'])
            print(f"  Found {len(materials)} materials")
            
            # Process and index PDFs
            stats = pdf_processor.process_course_materials(course['id'])
            
            for key in total_stats:
                total_stats[key] += stats[key]
            
            print(f"  Indexed: {stats['pdfs_found']} PDFs, {stats['chunks_indexed']} chunks")
            
        except Exception as e:
            print(f"  Error processing {course['name']}: {e}")
    
    print(f"\n✅ Vectorstore rebuild complete!")
    print(f"   Total materials: {total_stats['materials_processed']}")
    print(f"   Total PDFs indexed: {total_stats['pdfs_found']}")
    print(f"   Total chunks: {total_stats['chunks_indexed']}")
    
if __name__ == "__main__":
    rebuild_vectorstore()
