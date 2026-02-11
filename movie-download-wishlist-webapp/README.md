# Movie Download Wishlist Web Application

This project provides a collaborative movie wishlist management system using AWS serverless architecture. Users can create movie wishlists, track download status, express interest in movies, and collaborate with other users through a secure web interface.

## Architecture Overview

The infrastructure consists of the following AWS components:

- **Amazon Cognito**: User authentication and authorization
- **DynamoDB Tables**: Storage for movies and user interests
- **Lambda Functions**: Serverless API backend for CRUD operations
- **API Gateway**: RESTful API with Cognito authorization
- **S3 + CloudFront**: Static website hosting with CDN
- **IAM Roles**: Secure access control between services
- **CloudWatch Logs**: Monitoring and debugging

## How It Works

1. **Authenticate**: Users log in through Amazon Cognito authentication
2. **Browse**: View all movies with their status (wishlist/downloaded) and interested users
3. **Add Movies**: Create new movie entries in the wishlist
4. **Express Interest**: Mark movies you want to download
5. **Update Status**: Toggle movies between wishlist and downloaded states
6. **Collaborate**: See which other users are interested in each movie
7. **Manage**: Delete movies from the list

## Workflow Diagram

```
┌─────────────┐
│   User      │
│  Browser    │
└──────┬──────┘
       │ HTTPS
       v
┌─────────────────┐
│  CloudFront     │
│  + S3 Bucket    │
│  (Frontend)     │
└──────┬──────────┘
       │ API Calls
       v
┌─────────────────┐
│  API Gateway    │
│  + Cognito Auth │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│ Lambda Functions│
│  - Create Movie │
│  - Get Movies   │
│  - Update Status│
│  - Add Interest │
│  - Delete Movie │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       v                 v
┌─────────────┐   ┌─────────────┐
│  DynamoDB   │   │  Cognito    │
│  - Movies   │   │  User Pool  │
│  - Interests│   └─────────────┘
└─────────────┘
```

## Prerequisites

- AWS Account
- Terraform >= 1.0 installed
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for Lambda development)
- Modern web browser

## Project Structure

```
movie-download-wishlist-webapp/
├── frontend/           # Web application (HTML, CSS, JavaScript)
│   ├── index.html     # Main application page
│   ├── app.js         # Application logic and API integration
│   ├── styles.css     # Responsive styling
│   └── README.md      # Frontend documentation
├── lambda/            # AWS Lambda functions
│   ├── src/          # Lambda function code
│   │   ├── shared/   # Shared utilities
│   │   ├── create_movie.py
│   │   ├── get_movies.py
│   │   ├── update_movie_status.py
│   │   ├── delete_movie.py
│   │   ├── add_interest.py
│   │   └── remove_interest.py
│   ├── tests/        # Unit and property-based tests
│   ├── requirements.txt
│   └── README.md     # Lambda documentation
├── terraform/         # Infrastructure as Code
│   ├── 01_variables.tf
│   ├── 02_providers.tf
│   ├── 03_cognito.tf
│   ├── 04_dynamodb.tf
│   ├── 05_iam.tf
│   ├── 06_lambda.tf
│   ├── 07_api_gateway.tf
│   ├── 08_s3_cloudfront.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── README.md     # Terraform documentation
└── README.md         # This file
```

## Deployment

### Step 1: Deploy Infrastructure

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Configure your variables in `terraform.tfvars`:
   - Set AWS region (default: eu-west-3)
   - Set environment name (dev/test/prod)
   - Adjust resource configurations as needed

4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

5. Note the output values:
   ```bash
   terraform output
   ```

### Step 2: Configure Frontend

1. Update the configuration in `frontend/app.js` with the Terraform outputs:
   ```javascript
   const CONFIG = {
       region: 'YOUR_REGION',
       userPoolId: 'YOUR_USER_POOL_ID',      // From terraform output
       clientId: 'YOUR_CLIENT_ID',            // From terraform output
       apiEndpoint: 'YOUR_API_ENDPOINT'       // From terraform output
   };
   ```

2. The frontend is automatically deployed to S3 and served via CloudFront

### Step 3: Create Users

Create users in Cognito User Pool:

```bash
# Via AWS CLI
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username john.doe \
  --user-attributes Name=email,Value=john@example.com \
  --temporary-password TempPass123!

# Or use AWS Console
```

## Usage

1. Access the application via the CloudFront URL (from Terraform outputs)

2. Log in with your Cognito credentials

3. Add movies to the wishlist using the form

4. Express interest in movies by clicking "Je veux ce film"

5. Toggle movie status between wishlist and downloaded

6. View which users are interested in each movie

7. Delete movies when no longer needed

## Features

### Authentication & Authorization
- Secure login with Amazon Cognito
- JWT token-based API authentication
- Session persistence across page reloads
- Automatic logout on token expiration

### Movie Management
- Create new movie entries
- View all movies with status and metadata
- Update movie status (wishlist ↔ downloaded)
- Delete movies with confirmation
- Real-time list refresh

### Interest Tracking
- Express interest in movies
- Remove interest when no longer needed
- View all interested users per movie
- Current user highlighted in the list
- Interest buttons hidden for downloaded movies

### User Experience
- Responsive design (desktop, tablet, mobile)
- French language interface
- Error handling and user feedback
- Loading states and empty states
- Confirmation dialogs for destructive actions

## API Endpoints

All endpoints require Cognito JWT token in Authorization header:

- `GET /movies` - List all movies
- `POST /movies` - Create new movie
- `PATCH /movies/{movieId}/status` - Update movie status
- `DELETE /movies/{movieId}` - Delete movie
- `POST /movies/{movieId}/interest` - Add user interest
- `DELETE /movies/{movieId}/interest` - Remove user interest

## Data Model

### Movies Table (DynamoDB)
- `movieId` (String, Primary Key) - UUID
- `title` (String) - Movie title
- `status` (String) - "wishlist" or "downloaded"
- `createdBy` (String) - Username of creator
- `createdAt` (Number) - Unix timestamp

### Interests Table (DynamoDB)
- `movieId` (String, Partition Key)
- `userId` (String, Sort Key)
- `createdAt` (Number) - Unix timestamp

## Testing

### Lambda Functions

```bash
cd lambda

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run property-based tests only
pytest -m property tests/
```

### Frontend

Test locally with a simple HTTP server:

```bash
cd frontend

# Using Python
python -m http.server 8000

# Using Node.js
npx http-server

# Using PHP
php -S localhost:8000
```

Then open http://localhost:8000 in your browser.

## Cost Considerations

- **Cognito**: Free tier includes 50,000 MAUs
- **DynamoDB**: Pay per request (on-demand pricing)
- **Lambda**: Free tier includes 1M requests/month
- **API Gateway**: Free tier includes 1M API calls/month
- **S3**: Storage costs for frontend files (minimal)
- **CloudFront**: Pay per request and data transfer

## Security Best Practices

- All API calls authenticated via Cognito JWT tokens
- HTTPS enforced via CloudFront
- CORS configured in API Gateway
- IAM roles follow least privilege principle
- DynamoDB tables encrypted at rest
- CloudWatch logging enabled for auditing

## Troubleshooting

- Check CloudWatch Logs for Lambda execution details
- Verify Cognito user pool configuration
- Ensure API Gateway authorizer is properly configured
- Check browser console for frontend errors
- Verify CORS settings if API calls fail
- Confirm DynamoDB table names match environment variables

## Cleanup

To destroy all resources and avoid AWS charges:

```bash
cd terraform
terraform destroy
```

**Warning:** This will permanently delete all data including movies and user interests.

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements

- Email notifications for new movies
- Movie categories and tags
- Search and filter functionality
- User profiles and preferences

## License

This project is provided as-is for educational and demonstration purposes.
