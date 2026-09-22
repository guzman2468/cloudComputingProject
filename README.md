  # Nebraska Chat

  **PLEASE WORK OFF OF THE DEVELOP BRANCH, commit here before merging to main**
  Nebraska Chat is a FastAPI web application with a vanilla HTML, CSS, and JavaScript frontend.

  ## Technology Stack

  - **FastAPI** — Backend web framework
  - **SQLAlchemy** — Database connection and session management
  - **PostgreSQL through Supabase** — Application database
  - **S3-compatible storage** — Future storage location for uploaded photos
  - **Vanilla HTML, CSS, and JavaScript** — Frontend
  - **Docker** — Reserved for the AWS ECS deployment workflow

  ## Current Project Status

  The project currently includes:

  - A FastAPI application
  - A Supabase PostgreSQL connection
  - A database connectivity test endpoint
  - A static frontend landing page
  - Local startup scripts for macOS/Linux and Windows
  - Docker configuration reserved for AWS ECS deployment

  The following features are planned but are not fully implemented yet:

  - User authentication
  - Chat conversations
  - Message persistence
  - Photo uploads
  - S3 integration
  - Database models and migrations
  - Automated tests
  - AWS ECS deployment configuration

  ---

  # Local Development Setup

  **Use the regular startup scripts for all local testing.**

  **Do not use `start-docker.sh` or `start-docker.bat` for normal local development.** Those scripts are reserved for the container workflow used when preparing the application for AWS ECS.

  ## Prerequisites

  Install:

  - Python 3
  - Git
  - Access to the Supabase PostgreSQL database

  Docker is **not required** for local testing.

  **NOTE** reach out to Alejandro for the supabase connection string and admin permissions on the actual database on supabase.

  ## macOS/Linux Setup

  From the project root:

  ```bash
  cp .env.example .env

  Open .env and add the Supabase database connection string:

  DATABASE_URL=your_supabase_database_connection_string

  Do not commit .env to Git.

  Make the scripts executable:

  chmod +x setup.sh start.sh

  Create the virtual environment and install dependencies:

  ./setup.sh

  Start the application:

  ./start.sh

  ## Windows Setup

  Copy .env.example to .env.

  Add the Supabase database connection string:

  DATABASE_URL=your_supabase_database_connection_string

  Do not commit .env to Git.

  Run the setup script:

  setup.bat

  Start the application:

  start.bat

  ## Local URLs

  Once the application is running:

  Landing page:
  http://localhost:8000/

  FastAPI documentation:
  http://localhost:8000/docs

  Health check:
  http://localhost:8000/api/health

  Database connection test:
  http://localhost:8000/db-test

  ———

  # Frontend Structure

  The frontend uses vanilla HTML, CSS, and JavaScript. There is currently no frontend framework or JavaScript compilation tool.

  Frontend source files belong in:

  frontend/
  ├── pages/
  ├── images/
  └── resources/

  When the application starts, the frontend preparation script copies these files into:

  app/static/
  ├── pages/
  ├── images/
  └── resources/

  Do not manually edit files in app/static/. They are generated from the files in frontend/.

  ## Page Files

  All page files belong directly in frontend/pages/.

  Each page should use the same filename for its HTML, CSS, and JavaScript files:

  frontend/pages/
  ├── home.html
  ├── home.css
  ├── home.js
  ├── login.html
  ├── login.css
  ├── login.js
  ├── dashboard.html
  ├── dashboard.css
  └── dashboard.js

  Do not create a separate folder for each page.

  ## Frontend Images

  Frontend-owned images belong in:

  frontend/images/

  Examples:

  frontend/images/
  ├── logo.png
  ├── chat-icon.svg
  └── profile-placeholder.jpg

  These should be images that are part of the application interface, such as logos, icons, or placeholders.

  User-uploaded photos should not be stored here. User-uploaded photos will eventually be stored in S3-compatible storage.

  ## Other Frontend Resources

  Other browser resources belong in:

  frontend/resources/

  Examples include:

  - Fonts
  - Web manifests
  - Client-side JSON files
  - Static configuration files
  - Other browser-delivered resources

  ———

  # Backend Structure

  app/
  ├── __init__.py
  ├── main.py
  ├── database.py
  └── static/
      ├── pages/
      ├── images/
      └── resources/

  ## Backend Files

  - app/main.py — Creates the FastAPI application and defines the current routes
  - app/database.py — Configures the SQLAlchemy connection to Supabase PostgreSQL
  - app/static/ — Generated frontend files served by FastAPI

  The current health endpoint is defined in app/main.py:

  @app.get("/api/health")
  def health_check():
      return {
          "status": "ok",
          "message": "Nebraska Chat is running"
      }

  The backend/ directory is reserved for future backend organization as the application grows.

  Potential future backend folders include:

  backend/
  ├── api/
  │   └── routes/
  ├── core/
  ├── database/
  ├── schemas/
  └── services/

  Possible responsibilities:

  - api/routes/ — API endpoint modules
  - core/ — Configuration and security
  - database/ — Models and database utilities
  - schemas/ — Request and response validation
  - services/ — Application logic and external integrations

  ———

  # Database

  The application connects to Supabase PostgreSQL using the DATABASE_URL environment variable.

  SQLAlchemy is responsible for:

  - Creating the database engine
  - Managing connections
  - Creating sessions
  - Executing SQL queries
  - Supporting future database models

  The database connection is tested through:

  GET /db-test

  The database currently does not have application models or migrations.

  Future database tables may include:

  - Users
  - Conversations
  - Messages
  - Photos
  - User profiles

  ———

  # S3 Photo Storage

  Uploaded photos should eventually be stored in S3-compatible storage rather than inside the repository or application container.

  The database should store photo metadata such as:

  photo_id
  user_id
  bucket_name
  object_key
  original_filename
  content_type
  file_size
  created_at

  The actual image file should remain in S3.

  The backend will eventually:

  1. Receive or authorize a photo upload.
  2. Upload the photo to S3.
  3. Save the S3 bucket and object key in Supabase PostgreSQL.
  4. Return a public URL or temporary signed URL to the frontend.

  S3 credentials must remain on the backend. They must never be placed in frontend JavaScript.

  ———

  # Environment Variables

  Environment variables belong in .env.

  Example:

  DATABASE_URL=your_supabase_database_connection_string
  S3_ENDPOINT_URL=your_s3_endpoint
  S3_REGION=your_s3_region
  S3_BUCKET_NAME=your_bucket_name
  S3_ACCESS_KEY_ID=your_access_key
  S3_SECRET_ACCESS_KEY=your_secret_key

  Never commit .env to Git.

  Never place the following in frontend files:

  - Database credentials
  - S3 secret keys
  - Supabase service-role keys
  - Private API keys
  - Other sensitive credentials

  ———

  # Docker and AWS ECS

  The Docker workflow is reserved for deploying the application as a container, including the future AWS ECS deployment.

  Do not use the Docker startup scripts for normal local testing.

  The regular local scripts are:

  macOS/Linux: ./start.sh
  Windows:     start.bat

  The Docker scripts are:

  macOS/Linux: ./start-docker.sh
  Windows:     start-docker.bat

  The Docker workflow:

  1. Builds the application image.
  2. Installs Python dependencies.
  3. Copies the frontend into app/static/.
  4. Starts FastAPI inside the container.
  5. Loads environment variables from .env.
  6. Allows the container to connect to Supabase and S3 remotely.

  There is no local PostgreSQL container because the application uses Supabase.

  For AWS ECS, the Docker image will eventually be pushed to a container registry such as Amazon ECR and referenced by an ECS task definition.

  ———

  ## Important Rules

  - Use start.sh or start.bat for local testing.
  - Reserve the Docker scripts for the AWS ECS container workflow.
  - Place frontend page files directly in frontend/pages/.
  - Place frontend-owned images in frontend/images/.
  - Place other browser resources in frontend/resources/.
  - Do not manually edit generated files in app/static/.
  - Do not commit .env.
  - Never expose database or S3 credentials to the frontend.

