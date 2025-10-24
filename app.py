import streamlit as st
import streamlit.components.v1 as components
import requests
import json

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Vonage Video Meeting", page_icon="📹", layout="wide")
st.title("📹 Vonage Video Meeting App")
st.markdown("---")

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("Meeting Options")

    backend_url = st.text_input(
        "Backend URL (FastAPI)",
        value="http://127.0.0.1:5000",
        help="Where your FastAPI server is running",
    )

    st.markdown("---")

    option = st.radio("Choose action:", ["Create New Meeting", "Join Existing Meeting"])

    username = st.text_input("Enter your name:", value="User")
    st.session_state.username = username  # Store username in state

    # Health check button
    if st.button("🔍 Test Backend Connection"):
        test_backend_health()


# ---------------------------
# State
# ---------------------------
for key in [
    "api_key",
    "application_id",
    "default_session_id",
    "current_meeting",
    "last_session_details",
]:
    if key not in st.session_state:
        st.session_state[key] = None


# ---------------------------
# Helper: Create New Session
# ---------------------------
def create_new_video_session():
    """Create a new video session using the updated API endpoint"""
    try:
        url = f"{backend_url}/api/sessions/create"
        st.info("Creating new video session...")
        resp = requests.post(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        st.session_state.api_key = data["api_key"]
        st.session_state.application_id = data["application_id"]
        st.session_state.default_session_id = data["session_id"]
        st.success("✅ New video session created successfully!")
        st.info(f"📋 Share this Session ID with others: {data['session_id']}")
        return data["session_id"]
    except Exception as e:
        st.error(f"❌ Failed to create video session: {e}")
        return None


# ---------------------------
# Helper: Join Existing Session
# ---------------------------
def join_existing_video_session(session_id: str):
    """Join an existing video session using the updated API endpoint"""
    try:
        url = f"{backend_url}/api/sessions/{session_id}"
        st.info(f"Validating video session {session_id}...")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        st.session_state.api_key = data["api_key"]
        st.session_state.application_id = data["application_id"]
        st.session_state.default_session_id = session_id
        st.success("✅ Video session validated successfully!")
        return True
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            st.error("❌ Video session not found. Please check the Session ID.")
        else:
            st.error(f"❌ Failed to validate video session: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Failed to join video session: {e}")
        return False


# ---------------------------
# Helper: Test Backend Health
# ---------------------------
def test_backend_health():
    """Test backend connection and display health status"""
    try:
        url = f"{backend_url}/api/health"
        st.info("Testing backend connection...")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        health_data = resp.json()

        st.success("✅ Backend connection successful!")

        # Display health information
        with st.expander("🔍 Backend Health Details"):
            st.json(health_data)

        return True
    except Exception as e:
        st.error(f"❌ Backend connection failed: {e}")
        st.warning("Please ensure the FastAPI server is running on the specified URL")
        return False


# ---------------------------
# Helper: Generate User Token
# ---------------------------
def generate_user_access_token(target_session_id=None):
    """Generate access token for joining video session using updated API endpoint"""
    current_username = st.session_state.get("username", username)

    params = {"username": current_username}
    if target_session_id:
        params["session_id"] = target_session_id

    try:
        resp = requests.get(
            f"{backend_url}/api/tokens/generate",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Return both the token AND the session_id the server used
        return data["token"], data["session_id"]
    except Exception as e:
        st.error(f"❌ Failed to generate access token: {e}")
        # Return Nones to indicate failure
        return None, None


# ---------------------------
# Main logic
# ---------------------------
col_main, col_sidebar = st.columns([3, 1])

with col_main:
    # Main UI
    if option == "Create New Meeting":
        st.subheader("Create a New Meeting")
        st.markdown("This will create a brand new video session.")
        if st.button("🚀 Start Meeting"):
            session_id = create_new_video_session()
            if session_id:
                token, _ = generate_user_access_token(session_id)
                if token:
                    st.session_state.current_meeting = {
                        "session_id": session_id,
                        "token": token,
                        "application_id": st.session_state.application_id,
                    }
                    st.success(
                        f"✅ Meeting created! Share session ID: **`{session_id}`**"
                    )
                    st.rerun()  # Re-run to show video component

    elif option == "Join Existing Meeting":
        st.subheader("Join an Existing Meeting")
        session_input = st.text_input("Enter Session ID to join:")
        if st.button("🔗 Join Meeting"):
            if not session_input.strip():
                st.warning("⚠️ Please enter a valid session ID")
            else:
                if join_existing_video_session(session_input.strip()):
                    token, _ = generate_user_access_token(session_input.strip())
                    if token:
                        st.session_state.current_meeting = {
                            "session_id": session_input.strip(),
                            "token": token,
                            "application_id": st.session_state.application_id,
                        }
                        st.success(
                            f"✅ Ready to join meeting **`{session_input.strip()}`**"
                        )
                        st.rerun()  # Re-run to show video component

    # Show session details if user just left a meeting
    if not st.session_state.current_meeting and st.session_state.get(
        "last_session_details"
    ):
        st.markdown("---")
        st.subheader("📊 Last Session Details")

        session_details = st.session_state.last_session_details

        if "error" in session_details:
            st.error(f"❌ Failed to get session details: {session_details['error']}")
        else:
            # Display session information in a nice format
            col1, col2 = st.columns(2)

            with col1:
                st.info("**Session Information**")
                st.write(
                    f"**Session ID:** `{session_details.get('session_id', 'N/A')}`"
                )
                st.write(
                    f"**API Key:** `{session_details.get('api_key', 'N/A')[:8]}...`"
                )
                st.write(
                    f"**Application ID:** `{session_details.get('application_id', 'N/A')[:8]}...`"
                )

            with col2:
                st.success("**Session Status**")
                if session_details.get("session"):
                    st.write("✅ Session is still active")
                    st.write("🔗 Others can still join with this Session ID")
                else:
                    st.write("ℹ️ Session information retrieved")

            # Show raw session data in expandable section
            with st.expander("🔍 View Raw Session Data"):
                st.json(session_details)

        # Button to clear session details
        if st.button("🗑️ Clear Session Details"):
            st.session_state.last_session_details = None
            st.rerun()

# ---------------------------
# Video Section
# ---------------------------
if st.session_state.current_meeting:
    meet = st.session_state.current_meeting

    # Use json.dumps() for robust string embedding into JavaScript
    token_js = json.dumps(meet["token"].strip())
    app_id_js = json.dumps(meet["application_id"].strip())
    session_js = json.dumps(meet["session_id"].strip())
    username_js = json.dumps(username.strip())

    with col_main:
        st.markdown("---")
        st.subheader(f"📹 In Meeting: {meet['session_id']}")

        # FIX: The following block of HTML is inside a Python f-string.
        # JavaScript template literal variables (${variable}) must be escaped for Python's f-string
        # using the $ and double-curly-brace syntax: $"""{'{'}variable{'}'}""".
        video_html = f"""
        <div style="display: flex; gap: 15px; min-height: 600px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            
            <style>
                /* Professional Meeting Layout Styles */
                .filter-btn {{
                    padding: 8px 15px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 500;
                    font-size: 12px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin: 0 4px;
                }}
                .filter-btn:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }}
                
                /* Main video area */
                .main-video-area {{
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    background: #1a1a1a;
                    border-radius: 12px;
                    overflow: hidden;
                    position: relative;
                    height: 700px;
                }}
                
                /* Main display - shows user camera by default, screen share when active */
                .main-display {{
                    height: 480px;
                    background: #000;
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                /* Screen sharing container - hidden initially */
                .screen-share-container {{
                    width: 100%;
                    height: 100%;
                    position: absolute;
                    top: 0;
                    left: 0;
                    display: none;
                }}
                
                /* Main publisher container - shows user camera as main display */
                .main-publisher {{
                    width: 100%;
                    height: 100%;
                    position: relative;
                }}
                
                /* Video grid for participants - Horizontal scrollable */
                .participants-grid {{
                    display: flex;
                    gap: 15px;
                    padding: 15px;
                    background: rgba(255,255,255,0.05);
                    height: 160px;
                    overflow-x: auto;
                    overflow-y: hidden;
                    align-items: center;
                }}
                
                /* Scrollbar styling for participants grid */
                .participants-grid::-webkit-scrollbar {{
                    height: 8px;
                }}
                .participants-grid::-webkit-scrollbar-track {{
                    background: rgba(255,255,255,0.1);
                    border-radius: 4px;
                }}
                .participants-grid::-webkit-scrollbar-thumb {{
                    background: rgba(255,255,255,0.3);
                    border-radius: 4px;
                }}
                .participants-grid::-webkit-scrollbar-thumb:hover {{
                    background: rgba(255,255,255,0.5);
                }}
                
                /* Individual video container - Fixed size for consistency */
                .video-container {{
                    position: relative;
                    border-radius: 8px;
                    overflow: hidden;
                    background: #333;
                    width: 200px;
                    height: 120px;
                    flex-shrink: 0;
                }}
                
                /* Placeholder for empty participants grid */
                .participants-placeholder {{
                    color: #888;
                    text-align: center;
                    font-style: italic;
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                }}
                
                /* Video name overlay */
                .video-name {{
                    position: absolute;
                    bottom: 8px;
                    left: 8px;
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 10;
                    font-weight: 500;
                }}
                
                /* Controls bar */
                .controls-bar {{
                    background: rgba(255,255,255,0.95);
                    padding: 12px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 8px;
                    border-top: 1px solid rgba(0,0,0,0.1);
                    height: 60px;
                }}
                
                /* Chat sidebar */
                .chat-sidebar {{
                    width: 340px;
                    background: white;
                    border-radius: 12px;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    border: 1px solid #e0e0e0;
                    height: 700px;
                }}
                
                /* Chat header */
                .chat-header {{
                    background: #f8f9fa;
                    padding: 16px;
                    border-bottom: 1px solid #e0e0e0;
                    border-radius: 12px 12px 0 0;
                    height: 70px;
                    box-sizing: border-box;
                }}
                
                /* Chat messages area */
                .chat-messages {{
                    flex: 1;
                    padding: 12px;
                    overflow-y: auto;
                    height: 500px;
                }}
                
                /* Chat input area */
                .chat-input-area {{
                    padding: 12px;
                    border-top: 1px solid #e0e0e0;
                    background: #f8f9fa;
                    border-radius: 0 0 12px 12px;
                    height: 70px;
                    box-sizing: border-box;
                }}
                
                /* Status indicator */
                .status-indicator {{
                    padding: 6px 10px;
                    background: rgba(255,255,255,0.9);
                    border-radius: 6px;
                    font-size: 11px;
                    margin: 2px;
                }}
                
                /* Screen share container */
                #screen-share-container .OT_publisher {{
                    width: 100% !important; 
                    height: 100% !important;
                }}
                
                /* Mini self-video when screen sharing */
                .mini-self-video {{
                    position: absolute;
                    top: 16px;
                    right: 16px;
                    width: 180px;
                    height: 135px;
                    border-radius: 8px;
                    overflow: hidden;
                    z-index: 30;
                    border: 2px solid #fff;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                    display: none;
                }}
                
                /* Responsive design */
                @media (max-width: 1200px) {{
                    .chat-sidebar {{
                        width: 280px;
                    }}
                    .self-video {{
                        width: 160px;
                        height: 120px;
                    }}
                }}
            </style>

            <!-- MAIN VIDEO AREA -->
            <div class="main-video-area">
                <!-- Main Display - User Camera by default, Screen Share when active -->
                <div class="main-display">
                    <!-- User's Camera as Main Display -->
                    <div class="main-publisher" id="main-publisher">
                        <div id="publisher" style="width: 100%; height: 100%;"></div>
                        <div class="video-name">You ({username})</div>
                    </div>
                    
                    <!-- Screen Share Container - Hidden initially -->
                    <div class="screen-share-container" id="screen-share-container">
                        <!-- Screen sharing video will appear here -->
                    </div>
                    
                    <!-- Mini Self Video when Screen Sharing -->
                    <div class="mini-self-video" id="mini-self-video">
                        <div id="mini-publisher" style="width: 100%; height: 100%;"></div>
                        <div class="video-name">You ({username})</div>
                    </div>
                </div>
                
                <!-- Participants Grid -->
                <div class="participants-grid" id="subscribers">
                    <!-- Other participants will be added here dynamically -->
                    <div class="participants-placeholder" id="participants-placeholder">
                        <div>👥 Other participants will appear here</div>
                        <small>Invite others using the session ID above</small>
                    </div>
                </div>
                
                <!-- Controls Bar -->
                <div class="controls-bar">
                    <div class="status-indicator" id="statusMessage">Filter: Ready</div>
                    <div class="status-indicator" id="screenStatusMessage">Screen: Ready</div>
                    
                    <!-- Professional Control Icons -->
                    <button id="applyBlurBtn" class="filter-btn" style="background-color: #f59e0b; color: white;" title="Apply Background Blur">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1L9 7V9C9 11.8 11.2 14 14 14H16C18.8 14 21 11.8 21 9Z"/>
                        </svg>
                    </button>
                    <button id="applyImageBtn" class="filter-btn" style="background-color: #3b82f6; color: white;" title="Change Background">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M21,17H7V3A1,1 0 0,1 8,2H20A1,1 0 0,1 21,3V17M3,19A1,1 0 0,0 4,20H18A1,1 0 0,0 19,19V7H17V19H4V7H2V19M15.5,10A1.5,1.5 0 0,0 14,11.5A1.5,1.5 0 0,0 15.5,13A1.5,1.5 0 0,0 17,11.5A1.5,1.5 0 0,0 15.5,10M13.5,15L10.5,11L8.5,13.5L11,17H16L13.5,15Z"/>
                        </svg>
                    </button>
                    <button id="clearFilterBtn" class="filter-btn" style="background-color: #6c757d; color: white;" title="Clear Filter">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                        </svg>
                    </button>
                    <button id="toggleScreenShareBtn" class="filter-btn" style="background-color: #28a745; color: white;" title="Share Screen">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M3,3H21A1,1 0 0,1 22,4V16A1,1 0 0,1 21,17H14L16,19V20H8V19L10,17H3A1,1 0 0,1 2,16V4A1,1 0 0,1 3,3M4,5V15H20V5H4Z"/>
                        </svg>
                    </button>
                </div>
            </div>
            
            <!-- CHAT SIDEBAR -->
            <div class="chat-sidebar">
                <div class="chat-header">
                    <h4 style="margin: 0; color: #333; font-size: 16px;">💬 Meeting Chat</h4>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;">
                        Session: {meet['session_id'][:8]}...
                    </div>
                </div>
                
                <div class="chat-messages" id="messages">
                    <div style="color: #666; text-align: center; padding: 20px; font-style: italic;">
                        Welcome to the meeting chat!<br>
                        <small>Send messages to all participants</small>
                    </div>
                </div>
                
                <div class="chat-input-area">
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="chatInput" placeholder="Type your message..." 
                               style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none;">
                        <button id="sendChatBtn" class="filter-btn" style="background-color: #007bff; color: white; padding: 10px 16px; border-radius: 6px;">
                            📤
                        </button>
                    </div>
                </div>
            </div>

        </div>
        
        <script src="https://unpkg.com/@vonage/client-sdk-video@latest/dist/js/opentok.js"></script>
        
        <script>
        // Variables are injected using JSON.dumps() for reliable string literals.
        var applicationId = {app_id_js};
        var sessionId = {session_js};
        var token = {token_js}; 
        var username = {username_js};

        var publisher = null; // Globally available camera publisher instance
        var screenPublisher = null; // Globally available screen publisher instance
        
        // CORS-friendly image URL for background replacement
        const PLACEHOLDER_IMAGE_URL = 'https://cdn.pixabay.com/photo/2025/10/09/14/14/muztagh-9883659_1280.jpg'; 
        
        // Function to update filter status message
        function updateStatus(message, color = '#6b7280') {{
            document.getElementById('statusMessage').innerHTML = "Filter Status: " + message;
            document.getElementById('statusMessage').style.color = color;
        }}

        // Function to update screen sharing status message
        function updateScreenStatus(message, color = '#6b7280') {{
            let elem = document.getElementById('screenStatusMessage');
            if (elem) {{
                elem.innerHTML = "Screen Share Status: " + message;
                elem.style.color = color;
            }}
        }}

        // Function to apply video filter
        async function applyVideoFilter(filterOptions, statusText) {{
            if (!publisher) {{
                updateStatus("Publisher not initialized.", 'red');
                return;
            }}

            if (!OT.hasMediaProcessorSupport()) {{
                updateStatus("❌ Video filters are not supported in this browser.", 'red');
                return;
            }}
            
            updateStatus("Applying " + statusText + "...", 'orange');

            try {{
                await publisher.applyVideoFilter(filterOptions);
                updateStatus(statusText + " applied successfully.", '#10b981'); // Green
            }} catch (error) {{
                console.error("Error applying video filter:", error);
                
                let errorMessage = error.message || error.name;

                if (filterOptions.type === 'backgroundReplacement') {{
                     errorMessage += ". (HINT: If this error persists, it's a deep browser CSP issue, or the network is blocking the image download.)";
                }}

                updateStatus("❌ Failed to apply " + statusText + ": " + errorMessage, 'red');
            }}
        }}

        // Function to clear video filter
        async function clearFilter() {{
            if (!publisher) {{
                return;
            }}
            
            updateStatus("Clearing filter...", 'orange');
            
            try {{
                await publisher.clearVideoFilter();
                updateStatus("Filter cleared.", '#6b7280');
            }} catch (error) {{
                console.error("Error clearing video filter:", error);
                updateStatus("❌ Failed to clear filter: " + (error.message || error.name), 'red');
            }}
        }}
        
        // Function to display a new message in the chat box
        function displayMessage(sender, message, isLocal = false) {{
            const messagesDiv = document.getElementById('messages');
            const messageElement = document.createElement('div');
            
            let nameColor = isLocal ? '#10b981' : '#3b82f6'; // Green for self, Blue for others
            let align = isLocal ? 'flex-end' : 'flex-start';
            let bgColor = isLocal ? '#e0f2f1' : '#eff6ff'; // Light green or light blue background

            messageElement.style.display = 'flex';
            messageElement.style.justifyContent = align;
            messageElement.style.marginBottom = '8px';

            // FIX: Switching to standard string concatenation to bypass Python f-string/JS template literal conflict
            messageElement.innerHTML = 
                '<div style="max-width: 80%; padding: 6px 10px; border-radius: 12px; background-color: ' + bgColor + '; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">' +
                    '<strong style="color: ' + nameColor + '; font-size: 0.9em;">' + sender + ':</strong>' + 
                    '<span style="display: block; font-size: 1em; margin-top: 2px;">' + message + '</span>' +
                '</div>';

            messagesDiv.appendChild(messageElement);
            // Scroll to the bottom
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}

        // Function to send a message using the Vonage Signaling API
        function sendMessage(session) {{
            const chatInput = document.getElementById('chatInput');
            const message = chatInput.value.trim();
            
            if (message === "") {{
                return;
            }}

            // Use session.signal() to send the message
            session.signal({{
                type: 'chat',
                data: JSON.stringify({{
                    sender: username,
                    text: message
                }})
            }}, function(error) {{
                if (error) {{
                    console.error('Error sending signal:', error.name, error.message);
                    displayMessage("SYSTEM", "Failed to send message: " + error.message, false);
                }} else {{
                    // Display the message locally immediately after successful signal send
                    displayMessage(username, message, true);
                    chatInput.value = ''; // Clear input field
                }}
            }});
        }}


        // Function to initialize and publish the screen
        function initAndPublishScreen(session, btn) {{
            const container = document.getElementById('screen-share-container');
            const mainPublisher = document.getElementById('main-publisher');
            const miniSelfVideo = document.getElementById('mini-self-video');
            
            // Show screen share container and hide main publisher
            container.style.display = 'block';
            mainPublisher.style.display = 'none';
            miniSelfVideo.style.display = 'block';

            // Create a dedicated div for the screen publisher instance
            let screenDiv = document.createElement('div');
            screenDiv.id = 'screenPublisherDiv';
            screenDiv.style.width = '100%';
            screenDiv.style.height = '100%';
            container.appendChild(screenDiv);
            
            // Move user camera to mini video
            const publisherElement = document.getElementById('publisher');
            const miniPublisherContainer = document.getElementById('mini-publisher');
            if (publisherElement) {{
                miniPublisherContainer.appendChild(publisherElement);
            }}

            // Initialize the screen publisher
            screenPublisher = OT.initPublisher(
                screenDiv.id, // Publish to the new dedicated div
                {{
                    videoSource: 'screen',
                    insertMode: 'append',
                    width: '100%',
                    height: '100%',
                    name: username + ' Screen',
                    style: {{ buttonDisplayMode: 'on' }}
                }},
                function(error) {{
                    if (error) {{
                        console.error("Screen Publisher init error:", error);
                        updateScreenStatus("❌ Failed to start screen sharing: " + error.message, 'red');
                        screenPublisher = null;
                        btn.disabled = false;
                        screenPlaceholder.style.display = 'block';
                        container.style.display = 'flex'; // Restore flex layout
                        screenDiv.remove();
                    }} else {{
                        // Success, now publish
                        session.publish(screenPublisher, function(publishError) {{
                            btn.disabled = false; // Re-enable button
                            if (publishError) {{
                                console.error("Screen Publish error:", publishError);
                                updateScreenStatus("❌ Failed to publish screen: " + publishError.message, 'red');
                                screenPublisher.destroy();
                                screenPublisher = null;
                                screenPlaceholder.style.display = 'block';
                                container.style.display = 'flex'; // Restore flex layout
                                screenDiv.remove();
                            }} else {{
                                // Successful publish
                                btn.innerText = 'Stop Sharing Screen';
                                btn.style.backgroundColor = '#d97706';
                                updateScreenStatus("Screen is being shared successfully.", '#10b981');
                            }}
                        }});
                        
                        // Listen for the stream being destroyed by the user via the native UI (e.g., in Chrome)
                        screenPublisher.on('streamDestroyed', function(event) {{
                            if (event.reason === 'mediaStopped' || event.reason === 'sessionDisconnected') {{
                                if (screenPublisher) {{
                                    session.unpublish(screenPublisher); // Ensure unpublish is called
                                    screenPublisher.destroy();
                                    screenPublisher = null;
                                    btn.innerText = 'Share Screen';
                                    btn.style.backgroundColor = '#059669';
                                    screenPlaceholder.style.display = 'block';
                                    container.style.display = 'flex'; // Restore flex layout
                                    updateScreenStatus("Screen sharing stopped by user action.", '#6b7280');
                                    // Remove the screen element
                                    let screenDivToRemove = document.getElementById('screenPublisherDiv');
                                    if(screenDivToRemove) screenDivToRemove.remove();
                                }}
                            }}
                        }});
                    }}
                }}
            );
        }}

        // Function to toggle screen sharing
        function toggleScreenShare(session) {{
            const btn = document.getElementById('toggleScreenShareBtn');
            const container = document.getElementById('screen-share-container');
            const mainPublisher = document.getElementById('main-publisher');
            const miniSelfVideo = document.getElementById('mini-self-video');
            const screenDiv = document.getElementById('screenPublisherDiv');

            if (screenPublisher) {{
                // Stop sharing - restore user camera as main display
                session.unpublish(screenPublisher);
                screenPublisher.destroy();
                screenPublisher = null;
                btn.style.backgroundColor = '#28a745';
                btn.title = 'Share Screen';
                
                // Hide screen share and mini video, show main publisher
                container.style.display = 'none';
                miniSelfVideo.style.display = 'none';
                mainPublisher.style.display = 'block';
                
                // Move user camera back to main display
                const publisherElement = document.getElementById('publisher');
                const mainPublisherContainer = document.getElementById('main-publisher');
                if (publisherElement && mainPublisherContainer) {{
                    mainPublisherContainer.appendChild(publisherElement);
                }}
                
                if(screenDiv) screenDiv.remove();
                updateScreenStatus("Screen sharing stopped.");

            }} else {{
                // Start sharing
                btn.disabled = true; // Disable button while starting
                updateScreenStatus("Checking screen sharing capability...", 'orange');

                OT.checkScreenSharingCapability(function(response) {{
                    if (!response.supported || response.extensionRequired) {{
                        updateScreenStatus("❌ Screen sharing failed: " + 
                            (response.supported ? "Browser extension required" : "Not supported in this browser."), 'red');
                        btn.disabled = false;
                        return;
                    }}
                    
                    // Capability check passed, proceed to publish
                    initAndPublishScreen(session, btn);
                }});
            }}
        }}

        // --- Connection Logic and Initialization (Wrapped in window.onload) ---
        window.addEventListener('load', function() {{
            var session = OT.initSession(applicationId, sessionId);

            // 1. Initialize Camera Publisher
            publisher = OT.initPublisher("publisher", {{ 
                insertMode: "append",
                width: "100%",
                height: "100%",
                name: username,
                style: {{ buttonDisplayMode: 'on' }}
            }});

            // 2. Add Event Listeners for Buttons
            document.getElementById('applyBlurBtn').addEventListener('click', () => applyVideoFilter({{
                type: 'backgroundBlur',
                blurStrength: 'low' 
            }}, 'Background Blur (Low)'));
            
            document.getElementById('applyImageBtn').addEventListener('click', () => applyVideoFilter({{
                type: 'backgroundReplacement',
                backgroundImgUrl: PLACEHOLDER_IMAGE_URL
            }}, 'Background Replacement'));
            
            document.getElementById('clearFilterBtn').addEventListener('click', clearFilter);

            // Screen Share Listener
            document.getElementById('toggleScreenShareBtn').addEventListener('click', () => toggleScreenShare(session));

            // 3. Add Signal Listener for Chat (Must be before session.connect)
            session.on('signal:chat', function(event) {{
                // Ignore signals sent from ourselves (they are already displayed locally in sendMessage)
                if (event.from.connectionId === session.connection.connectionId) {{
                    return;
                }}
                
                try {{
                    const data = JSON.parse(event.data);
                    displayMessage(data.sender, data.text, false); // false = not local
                }} catch (e) {{
                    console.error("Error parsing signal data:", e);
                }}
            }});


            // 4. Connect to Session
            session.connect(token, function(error) {{
                if (error) {{
                    console.error("Connection error:", error);
                    document.getElementById('publisher-container').innerHTML = 
                        '<div style="color:#ef4444; background-color:#fef2f2; border: 1px solid #fca5a5; padding: 15px; border-radius: 5px; font-family: sans-serif;">' +
                        '❌ **Connection Failed**' +
                        '<br>Error: ' + error.message + ' (Code: ' + error.code + ')' +
                        '<br><br>Check the server logs and confirm the API Key/Token/Session ID are correct.' +
                        '</div>';
                }} else {{
                    console.log("Session connected successfully.");
                    session.publish(publisher);
                }}
            }});

            // 5. Handle Streams (Subscribers) - Horizontal Scrollable Layout
            session.on('streamCreated', function(event) {{
                console.log("New stream created:", event.stream.name);
                
                const subscribersGrid = document.getElementById('subscribers');
                
                // Remove placeholder when first participant joins
                const placeholder = document.getElementById('participants-placeholder');
                if (placeholder) {{
                    placeholder.remove();
                }}
                
                // Create container for video
                var videoContainer = document.createElement('div');
                videoContainer.className = 'video-container';
                videoContainer.id = 'stream-' + event.stream.streamId;
                
                // Create name overlay
                var nameOverlay = document.createElement('div');
                nameOverlay.className = 'video-name';
                nameOverlay.textContent = event.stream.name || 'Participant';
                
                videoContainer.appendChild(nameOverlay);
                subscribersGrid.appendChild(videoContainer);
                
                // Subscribe to the stream
                session.subscribe(event.stream, videoContainer, {{
                    insertMode: 'append',
                    width: '100%',
                    height: '100%',
                    style: {{
                        buttonDisplayMode: 'off'
                    }}
                }});
                
                // Auto-scroll to show new participant
                subscribersGrid.scrollLeft = subscribersGrid.scrollWidth;
            }});
            
            session.on("streamDestroyed", function(event) {{
                console.log("Stream destroyed:", event.stream.name);
                var subDiv = document.getElementById("stream-" + event.stream.streamId);
                if (subDiv) {{
                    subDiv.remove();
                }}
            }});

            // 6. Add Event Listeners for Chat
            const chatInput = document.getElementById('chatInput');
            const sendChatBtn = document.getElementById('sendChatBtn');
            
            sendChatBtn.addEventListener('click', () => sendMessage(session));
            
            chatInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    e.preventDefault(); // Prevent newline in input
                    sendMessage(session);
                }}
            }});


        }}); // End of window.onload
        </script>
        """

        components.html(
            video_html, height=750, scrolling=False
        )  # Increased height for better video display

    st.markdown("---")
    if st.button("🚪 Leave Meeting"):
        # Get session details before leaving
        session_id = st.session_state.current_meeting["session_id"]
        try:
            url = f"{backend_url}/api/sessions/{session_id}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            session_details = resp.json()

            # Store session details to show after leaving
            st.session_state.last_session_details = session_details
        except Exception as e:
            st.session_state.last_session_details = {"error": str(e)}

        # Clear current meeting
        st.session_state.current_meeting = None
        st.rerun()

with col_sidebar:
    st.info(
        "💡 To test multi-user, open multiple tabs and join with different usernames. You can share your camera and screen simultaneously."
    )
    if st.session_state.application_id:
        st.subheader("Session Info")
        st.write(f"**Application ID:** `{st.session_state.application_id[:5]}...`")
        st.code(st.session_state.default_session_id, language=None)
