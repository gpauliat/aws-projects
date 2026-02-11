# Movie Download Wishlist - Frontend

This is the frontend application for the Movie Download Wishlist system.

## Technology Stack

- **HTML5**: Structure and layout
- **CSS3**: Styling with responsive design
- **Vanilla JavaScript**: Application logic
- **Amazon Cognito Identity SDK**: User authentication

## Project Structure

```
frontend/
├── index.html      # Main HTML file
├── styles.css      # CSS styles
├── app.js          # JavaScript application logic
└── README.md       # This file
```

## Configuration

Before deploying, you need to update the configuration in `app.js`:

```javascript
const CONFIG = {
    region: 'eu-west-3',
    userPoolId: 'YOUR_USER_POOL_ID',  // From terraform output: cognito_user_pool_id
    clientId: 'YOUR_CLIENT_ID',        // From terraform output: cognito_user_pool_client_id
    apiEndpoint: 'YOUR_API_ENDPOINT'   // From terraform output: api_gateway_invoke_url
};
```

### Getting Configuration Values

After running `terraform apply`, get the values:

```bash
cd terraform
terraform output cognito_user_pool_id
terraform output cognito_user_pool_client_id
terraform output api_gateway_invoke_url
```

## Features

### Authentication
- Login form with username and password
- JWT token storage and management
- Session persistence across page reloads
- Logout functionality
- Automatic redirect to login when session expires

### Movie List Display
- Displays all movies with title, status, and interested users
- Shows "No movies yet" message when list is empty
- Refresh button to reload movies
- Error handling and display

### Add Movie
- Form to add new movies
- Client-side validation (non-empty title)
- Success/error message display
- Automatic list refresh after adding

### Movie Status Toggle
- Toggle button for each movie
- Switches between "wishlist" and "downloaded"
- Optimistic UI updates
- Error handling with revert on failure

### Interest Tracking
- "I Want This" button to express interest
- "Remove Interest" button when already interested
- Display of all interested users
- Current user highlighted in green

### Delete Movie
- Delete button for each movie
- Confirmation dialog before deletion
- Automatic list refresh after deletion
- Error handling

## Local Development

To test locally, you can use a simple HTTP server:

```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx http-server

# Using PHP
php -S localhost:8000
```

Then open http://localhost:8000 in your browser.

## Deployment to S3

The frontend will be deployed to S3 with CloudFront using Terraform (Section 6).

## API Endpoints Used

- `GET /movies` - List all movies
- `POST /movies` - Create new movie
- `PATCH /movies/{movieId}/status` - Update movie status
- `DELETE /movies/{movieId}` - Delete movie
- `POST /movies/{movieId}/interest` - Add user interest
- `DELETE /movies/{movieId}/interest` - Remove user interest

All endpoints require authentication via Cognito JWT token in the Authorization header.

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security

- All API calls include JWT token in Authorization header
- Automatic logout on token expiration (401 response)
- HTTPS enforced via CloudFront
- CORS configured in API Gateway

## Responsive Design

The application is fully responsive and works on Desktop, Tablet and Mobile
