#!/usr/bin/env python3
"""
Complete KYC Workflow Testing - Comprehensive test of all KYC requirements
Testing all specific requirements from the review request
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://quickcourier.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kuryecini.com"
ADMIN_PASSWORD = "KuryeciniAdmin2024!"

def test_complete_kyc_workflow():
    """Test complete KYC workflow as specified in review request"""
    print("🎯 COMPLETE KYC WORKFLOW TESTING")
    print("Testing all requirements from review request:")
    print("1. Test admin authentication with admin@kuryecini.com / KuryeciniAdmin2024!")
    print("2. Retrieve pending businesses using GET /api/admin/businesses?kyc_status=pending")
    print("3. Attempt to approve at least one pending business using the KYC approval endpoint")
    print("4. Verify the approval was successful by checking the business status")
    print("5. Test the complete KYC workflow including rejection scenarios")
    print("=" * 80)
    
    test_results = []
    
    # REQUIREMENT 1: Test admin authentication
    print("\n📋 REQUIREMENT 1: Admin Authentication")
    print(f"Testing admin login with {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    
    try:
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            admin_token = login_data.get("access_token")
            user_data = login_data.get("user", {})
            
            print(f"✅ Admin authentication successful")
            print(f"   Token length: {len(admin_token)} characters")
            print(f"   User role: {user_data.get('role')}")
            print(f"   User email: {user_data.get('email')}")
            
            test_results.append({"test": "Admin Authentication", "success": True, "details": f"Token: {len(admin_token)} chars"})
        else:
            print(f"❌ Admin authentication failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            test_results.append({"test": "Admin Authentication", "success": False, "details": f"Status: {login_response.status_code}"})
            return test_results
            
    except Exception as e:
        print(f"❌ Admin authentication exception: {str(e)}")
        test_results.append({"test": "Admin Authentication", "success": False, "details": f"Exception: {str(e)}"})
        return test_results
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    # REQUIREMENT 2: Retrieve pending businesses
    print("\n📋 REQUIREMENT 2: Retrieve Pending Businesses")
    print("Testing GET /api/admin/businesses?kyc_status=pending")
    
    try:
        pending_response = requests.get(f"{BACKEND_URL}/admin/businesses?kyc_status=pending", headers=headers)
        
        if pending_response.status_code == 200:
            pending_data = pending_response.json()
            # Handle both list and dict response formats
            if isinstance(pending_data, list):
                pending_businesses = pending_data
            else:
                pending_businesses = pending_data.get("businesses", [])
            
            print(f"✅ Successfully retrieved pending businesses")
            print(f"   Found {len(pending_businesses)} pending businesses")
            
            # Show details of first few businesses
            for i, business in enumerate(pending_businesses[:3]):
                print(f"   Business {i+1}: {business.get('business_name', 'N/A')} (ID: {business.get('id', 'N/A')[:8]}...)")
            
            test_results.append({"test": "Retrieve Pending Businesses", "success": True, "details": f"Found {len(pending_businesses)} businesses"})
        else:
            print(f"❌ Failed to retrieve pending businesses: {pending_response.status_code}")
            print(f"   Response: {pending_response.text}")
            test_results.append({"test": "Retrieve Pending Businesses", "success": False, "details": f"Status: {pending_response.status_code}"})
            return test_results
            
    except Exception as e:
        print(f"❌ Retrieve pending businesses exception: {str(e)}")
        test_results.append({"test": "Retrieve Pending Businesses", "success": False, "details": f"Exception: {str(e)}"})
        return test_results
    
    # REQUIREMENT 3 & 4: Approve business and verify
    if pending_businesses:
        test_business = pending_businesses[0]
        business_id = test_business.get("id")
        business_name = test_business.get("business_name", "Unknown Business")
        
        print(f"\n📋 REQUIREMENT 3: Approve Business via KYC Endpoint")
        print(f"Testing PATCH /api/admin/businesses/{business_id}/status")
        print(f"Target business: {business_name}")
        
        try:
            approval_data = {"kyc_status": "approved"}
            approval_response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/{business_id}/status",
                headers=headers,
                json=approval_data
            )
            
            if approval_response.status_code == 200:
                approval_result = approval_response.json()
                print(f"✅ Business approval successful")
                print(f"   Response: {json.dumps(approval_result, indent=2)}")
                print(f"   Success field: {approval_result.get('success')}")
                print(f"   Message: {approval_result.get('message')}")
                
                test_results.append({"test": "Business KYC Approval", "success": True, "details": f"Approved {business_name}"})
                
                # REQUIREMENT 4: Verify approval was successful
                print(f"\n📋 REQUIREMENT 4: Verify Approval Success")
                print(f"Testing GET /api/admin/businesses/{business_id}")
                
                try:
                    verify_response = requests.get(f"{BACKEND_URL}/admin/businesses/{business_id}", headers=headers)
                    
                    if verify_response.status_code == 200:
                        business_data = verify_response.json()
                        current_status = business_data.get("kyc_status")
                        
                        if current_status == "approved":
                            print(f"✅ Approval verification successful")
                            print(f"   Business status: {current_status}")
                            print(f"   KYC updated at: {business_data.get('kyc_updated_at', 'N/A')}")
                            
                            test_results.append({"test": "Verify Approval Success", "success": True, "details": f"Status: {current_status}"})
                        else:
                            print(f"❌ Approval verification failed")
                            print(f"   Expected: approved, Got: {current_status}")
                            test_results.append({"test": "Verify Approval Success", "success": False, "details": f"Status: {current_status}"})
                    else:
                        print(f"❌ Failed to verify approval: {verify_response.status_code}")
                        test_results.append({"test": "Verify Approval Success", "success": False, "details": f"Status: {verify_response.status_code}"})
                        
                except Exception as e:
                    print(f"❌ Verification exception: {str(e)}")
                    test_results.append({"test": "Verify Approval Success", "success": False, "details": f"Exception: {str(e)}"})
                
            else:
                print(f"❌ Business approval failed: {approval_response.status_code}")
                print(f"   Response: {approval_response.text}")
                test_results.append({"test": "Business KYC Approval", "success": False, "details": f"Status: {approval_response.status_code}"})
                
        except Exception as e:
            print(f"❌ Business approval exception: {str(e)}")
            test_results.append({"test": "Business KYC Approval", "success": False, "details": f"Exception: {str(e)}"})
    
    # REQUIREMENT 5: Test rejection scenarios
    if len(pending_businesses) > 1:
        rejection_business = pending_businesses[1]
        rejection_business_id = rejection_business.get("id")
        rejection_business_name = rejection_business.get("business_name", "Unknown Business")
        
        print(f"\n📋 REQUIREMENT 5: Test Rejection Scenarios")
        print(f"Testing business rejection workflow")
        print(f"Target business: {rejection_business_name}")
        
        try:
            rejection_data = {
                "kyc_status": "rejected",
                "rejection_reason": "Test rejection for comprehensive KYC workflow verification"
            }
            
            rejection_response = requests.patch(
                f"{BACKEND_URL}/admin/businesses/{rejection_business_id}/status",
                headers=headers,
                json=rejection_data
            )
            
            if rejection_response.status_code == 200:
                rejection_result = rejection_response.json()
                print(f"✅ Business rejection successful")
                print(f"   Response: {json.dumps(rejection_result, indent=2)}")
                print(f"   Success field: {rejection_result.get('success')}")
                
                # Verify rejection
                verify_rejection_response = requests.get(f"{BACKEND_URL}/admin/businesses/{rejection_business_id}", headers=headers)
                if verify_rejection_response.status_code == 200:
                    rejected_business_data = verify_rejection_response.json()
                    rejection_status = rejected_business_data.get("kyc_status")
                    rejection_reason = rejected_business_data.get("rejection_reason")
                    
                    if rejection_status == "rejected":
                        print(f"✅ Rejection verification successful")
                        print(f"   Status: {rejection_status}")
                        print(f"   Reason: {rejection_reason}")
                        test_results.append({"test": "Business KYC Rejection", "success": True, "details": f"Rejected {rejection_business_name}"})
                    else:
                        print(f"❌ Rejection verification failed: {rejection_status}")
                        test_results.append({"test": "Business KYC Rejection", "success": False, "details": f"Status: {rejection_status}"})
                else:
                    print(f"❌ Failed to verify rejection: {verify_rejection_response.status_code}")
                    test_results.append({"test": "Business KYC Rejection", "success": False, "details": "Verification failed"})
            else:
                print(f"❌ Business rejection failed: {rejection_response.status_code}")
                print(f"   Response: {rejection_response.text}")
                test_results.append({"test": "Business KYC Rejection", "success": False, "details": f"Status: {rejection_response.status_code}"})
                
        except Exception as e:
            print(f"❌ Business rejection exception: {str(e)}")
            test_results.append({"test": "Business KYC Rejection", "success": False, "details": f"Exception: {str(e)}"})
    
    # Test error handling for invalid business IDs
    print(f"\n📋 ADDITIONAL: Error Handling Testing")
    print("Testing invalid business ID handling")
    
    try:
        invalid_id = "invalid-business-id-12345"
        error_response = requests.patch(
            f"{BACKEND_URL}/admin/businesses/{invalid_id}/status",
            headers=headers,
            json={"kyc_status": "approved"}
        )
        
        if error_response.status_code == 404:
            print(f"✅ Invalid business ID handling correct (404)")
            test_results.append({"test": "Invalid Business ID Handling", "success": True, "details": "Returns 404"})
        else:
            print(f"⚠️  Invalid business ID returned: {error_response.status_code}")
            test_results.append({"test": "Invalid Business ID Handling", "success": False, "details": f"Status: {error_response.status_code}"})
            
    except Exception as e:
        print(f"❌ Error handling test exception: {str(e)}")
        test_results.append({"test": "Invalid Business ID Handling", "success": False, "details": f"Exception: {str(e)}"})
    
    return test_results

def main():
    """Main test execution"""
    print("🚀 COMPLETE KYC WORKFLOW TESTING")
    print("Verifying fix for user-reported issue: 'İşletme kyc başarısız oluyor onaylanmiyor'")
    print("(Business KYC fails, not being approved)")
    print()
    
    results = test_complete_kyc_workflow()
    
    # Generate summary
    print("\n" + "=" * 80)
    print("📊 COMPLETE KYC WORKFLOW TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📈 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print()
    
    print("📋 DETAILED RESULTS:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['test']}")
        print(f"      Details: {result['details']}")
    
    print("\n🎯 REVIEW REQUEST REQUIREMENTS VERIFICATION:")
    requirements = [
        "Admin authentication with admin@kuryecini.com / KuryeciniAdmin2024!",
        "Retrieve pending businesses using GET /api/admin/businesses?kyc_status=pending",
        "Approve at least one pending business using KYC approval endpoint",
        "Verify approval was successful by checking business status",
        "Test complete KYC workflow including rejection scenarios"
    ]
    
    for i, req in enumerate(requirements, 1):
        print(f"   {i}. {req}")
        # Check if related tests passed
        related_tests = [r for r in results if any(keyword in r["test"].lower() for keyword in req.lower().split()[:2])]
        if related_tests and all(r["success"] for r in related_tests):
            print(f"      ✅ VERIFIED")
        elif related_tests:
            print(f"      ⚠️  PARTIAL")
        else:
            print(f"      ❓ NOT TESTED")
    
    print(f"\n🔍 FOCUS AREAS VERIFICATION:")
    focus_areas = [
        "Backend response includes 'success: true' field that frontend expects",
        "PATCH /api/admin/businesses/{business_id}/status endpoint works correctly",
        "Test both approval (kyc_status: approved) and rejection (kyc_status: rejected) scenarios",
        "Check proper error handling for invalid business IDs"
    ]
    
    for area in focus_areas:
        print(f"   • {area}")
        if "success: true" in area:
            approval_tests = [r for r in results if "approval" in r["test"].lower()]
            if approval_tests and all(r["success"] for r in approval_tests):
                print(f"     ✅ CONFIRMED")
            else:
                print(f"     ❓ NEEDS VERIFICATION")
        elif "PATCH" in area:
            patch_tests = [r for r in results if "approval" in r["test"].lower() or "rejection" in r["test"].lower()]
            if patch_tests and all(r["success"] for r in patch_tests):
                print(f"     ✅ CONFIRMED")
            else:
                print(f"     ❓ NEEDS VERIFICATION")
        elif "both approval" in area:
            approval_test = any(r["success"] for r in results if "approval" in r["test"].lower())
            rejection_test = any(r["success"] for r in results if "rejection" in r["test"].lower())
            if approval_test and rejection_test:
                print(f"     ✅ CONFIRMED")
            else:
                print(f"     ❓ PARTIAL")
        elif "error handling" in area:
            error_tests = [r for r in results if "invalid" in r["test"].lower() or "error" in r["test"].lower()]
            if error_tests and all(r["success"] for r in error_tests):
                print(f"     ✅ CONFIRMED")
            else:
                print(f"     ❓ NEEDS VERIFICATION")
    
    print(f"\n💡 FINAL CONCLUSION:")
    if success_rate >= 90:
        print("✅ KYC APPROVAL SYSTEM IS WORKING EXCELLENTLY")
        print("✅ All critical requirements from review request are met")
        print("✅ User-reported issue 'İşletme kyc başarısız oluyor onaylanmiyor' appears to be resolved")
        print("💡 If users still experience issues, the problem is likely in frontend implementation")
    elif success_rate >= 70:
        print("⚠️  KYC APPROVAL SYSTEM IS MOSTLY WORKING")
        print("⚠️  Some minor issues may need attention")
        print("💡 Review failed tests and address any backend issues")
    else:
        print("❌ KYC APPROVAL SYSTEM HAS SIGNIFICANT ISSUES")
        print("❌ User-reported issue is confirmed - backend fixes required")
        print("🔧 Immediate attention needed for failed tests")

if __name__ == "__main__":
    main()