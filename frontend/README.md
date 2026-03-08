# MemoryLens Frontend

This directory contains the user interface for MemoryLens.

The main application resides in the `memorylens-ui` folder, which is a React application created with React (e.g., Vite/CRA).

## Setup Instructions

1.  **Navigate to the UI folder**:
    ```bash
    cd memorylens-ui
    ```

2.  **Install Dependencies**:
    Make sure you have Node.js and npm installed.
    ```bash
    npm install
    ```

3.  **Run the Development Server**:
    ```bash
    npm start
    # OR depending on the package.json setup:
    # npm run dev
    ```

    This will start the frontend on a local development server (typically `http://localhost:3000` or `http://localhost:5173`).

## Features

*   **Unified Search Interface**: Easily search through indexed documents and photos from a single search bar.
*   **Indexing Controls**: A UI panel to trigger the backend to index a new directory of files.
*   **Real-time Progress**: Displays the indexing progress as the backend processes large folders of images and documents.
