A secure file-sharing system between two different types of users:

REST API’s are created for the following actions.

User 1: Operation User
Action which could be done by an Ops User
1. Login
2. Upload File*
* Only Ops User is allowed to upload pptx,docx and xlsx * 
Upload file must be only of pptx,docx, and xlsx type

User 2: Client User
Action which could be done by a Client User
1. Sign Up ( Return an encrypted URL )
2. Email Verify ( Verification Email will be sent to the user on the registered email )
3. Login
4. Download File
5. List all uploaded files
