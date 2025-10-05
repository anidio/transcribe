import requests
import sys
import json
from datetime import datetime

class YouTubeAIProcessorTester:
    def __init__(self, base_url="https://ytsummary-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                print(f"   Status: {response.status_code} ✅")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print("   Response: Non-JSON response")
            else:
                print(f"   Status: {response.status_code} ❌ (Expected {expected_status})")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")

            self.log_test(name, success, f"Status: {response.status_code}, Expected: {expected_status}")
            return success, response.json() if success else {}

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout}s"
            print(f"   ⏰ {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}
        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            print(f"   💥 {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_transcribe_video(self):
        """Test video transcription with a real YouTube URL"""
        # Using a short, popular YouTube video for testing
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video
        
        success, response = self.run_test(
            "Video Transcription",
            "POST",
            "videos/transcribe",
            200,
            data={"url": test_url},
            timeout=60  # Longer timeout for transcription
        )
        
        if success and response:
            # Check if response has required fields
            required_fields = ['id', 'url', 'transcript', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields in response: {missing_fields}")
                self.log_test("Transcription Response Structure", False, f"Missing fields: {missing_fields}")
            else:
                print(f"   📝 Transcript length: {len(response.get('transcript', ''))} characters")
                self.log_test("Transcription Response Structure", True, "All required fields present")
        
        return success, response

    def test_transcribe_invalid_url(self):
        """Test transcription with invalid YouTube URL"""
        success, response = self.run_test(
            "Invalid URL Handling",
            "POST",
            "videos/transcribe",
            400,
            data={"url": "https://invalid-url.com"}
        )
        return success

    def test_summarize_text(self, transcript_text=None):
        """Test text summarization"""
        if not transcript_text:
            transcript_text = "This is a test transcript for summarization. It contains some sample content that should be processed by the AI system to generate a meaningful summary."
        
        success, response = self.run_test(
            "Text Summarization",
            "POST",
            "videos/summarize",
            200,
            data={"text": transcript_text},
            timeout=60  # Longer timeout for AI processing
        )
        
        if success and response:
            # Check response structure
            required_fields = ['id', 'result', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields in response: {missing_fields}")
                self.log_test("Summarization Response Structure", False, f"Missing fields: {missing_fields}")
            else:
                print(f"   📄 Summary length: {len(response.get('result', ''))} characters")
                self.log_test("Summarization Response Structure", True, "All required fields present")
        
        return success, response

    def test_summarize_empty_text(self):
        """Test summarization with empty text"""
        success, response = self.run_test(
            "Empty Text Summarization",
            "POST",
            "videos/summarize",
            400,
            data={"text": ""}
        )
        return success

    def test_enrich_text(self, transcript_text=None):
        """Test text enrichment"""
        if not transcript_text:
            transcript_text = "This is a test transcript for enrichment. It contains basic information that should be enhanced and structured by the AI system."
        
        success, response = self.run_test(
            "Text Enrichment",
            "POST",
            "videos/enrich",
            200,
            data={"text": transcript_text},
            timeout=60  # Longer timeout for AI processing
        )
        
        if success and response:
            # Check response structure
            required_fields = ['id', 'result', 'timestamp']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"   ⚠️  Missing fields in response: {missing_fields}")
                self.log_test("Enrichment Response Structure", False, f"Missing fields: {missing_fields}")
            else:
                print(f"   ✨ Enrichment length: {len(response.get('result', ''))} characters")
                self.log_test("Enrichment Response Structure", True, "All required fields present")
        
        return success, response

    def test_enrich_empty_text(self):
        """Test enrichment with empty text"""
        success, response = self.run_test(
            "Empty Text Enrichment",
            "POST",
            "videos/enrich",
            400,
            data={"text": ""}
        )
        return success

    def test_get_videos(self):
        """Test getting all videos"""
        success, response = self.run_test(
            "Get All Videos",
            "GET",
            "videos",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   📊 Found {len(response)} videos in database")
            self.log_test("Videos List Structure", True, f"Returned {len(response)} videos")
        elif success:
            print(f"   ⚠️  Expected list, got {type(response)}")
            self.log_test("Videos List Structure", False, f"Expected list, got {type(response)}")
        
        return success

    def run_full_workflow_test(self):
        """Test the complete workflow: transcribe -> summarize -> enrich"""
        print("\n🔄 Running Full Workflow Test...")
        
        # Step 1: Transcribe
        transcribe_success, transcribe_response = self.test_transcribe_video()
        if not transcribe_success:
            self.log_test("Full Workflow", False, "Transcription failed")
            return False
        
        transcript_text = transcribe_response.get('transcript', '')
        if not transcript_text:
            self.log_test("Full Workflow", False, "No transcript text received")
            return False
        
        # Step 2: Summarize
        summarize_success, summarize_response = self.test_summarize_text(transcript_text)
        if not summarize_success:
            self.log_test("Full Workflow", False, "Summarization failed")
            return False
        
        # Step 3: Enrich
        enrich_success, enrich_response = self.test_enrich_text(transcript_text)
        if not enrich_success:
            self.log_test("Full Workflow", False, "Enrichment failed")
            return False
        
        self.log_test("Full Workflow", True, "Complete workflow successful")
        return True

def main():
    print("🚀 Starting YouTube AI Processor Backend Tests")
    print("=" * 60)
    
    tester = YouTubeAIProcessorTester()
    
    # Basic API tests
    print("\n📡 Testing Basic API Endpoints...")
    tester.test_root_endpoint()
    
    # Video processing tests
    print("\n🎥 Testing Video Processing...")
    tester.test_transcribe_invalid_url()  # Test error handling first
    
    # AI processing tests
    print("\n🤖 Testing AI Processing...")
    tester.test_summarize_empty_text()  # Test error handling
    tester.test_enrich_empty_text()     # Test error handling
    
    # Test with sample text (faster than full video)
    sample_text = "Este é um texto de exemplo para testar as funcionalidades de IA. Contém informações básicas que devem ser processadas pelo sistema de inteligência artificial para gerar resumos e aprimoramentos significativos."
    tester.test_summarize_text(sample_text)
    tester.test_enrich_text(sample_text)
    
    # Database tests
    print("\n💾 Testing Database Operations...")
    tester.test_get_videos()
    
    # Full workflow test (this will take longer due to real YouTube transcription)
    print("\n🔄 Testing Complete Workflow...")
    print("⚠️  This test uses a real YouTube video and may take 1-2 minutes...")
    tester.run_full_workflow_test()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    # Save detailed results
    results_file = "/app/test_reports/backend_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "tests_run": tester.tests_run,
                "tests_passed": tester.tests_passed,
                "success_rate": tester.tests_passed/tester.tests_run*100,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": tester.test_results
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: {results_file}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())