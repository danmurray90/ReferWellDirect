/**
 * Real-time notifications client for ReferWell Direct.
 */
class NotificationClient {
  constructor(options = {}) {
    this.options = {
      websocketUrl: options.websocketUrl || "/ws/notifications/",
      sseUrl: options.sseUrl || "/api/notifications/sse/",
      reconnectInterval: options.reconnectInterval || 5000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      onNotification: options.onNotification || this.defaultNotificationHandler,
      onError: options.onError || this.defaultErrorHandler,
      onConnect: options.onConnect || this.defaultConnectHandler,
      onDisconnect: options.onDisconnect || this.defaultDisconnectHandler,
    };

    this.websocket = null;
    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.isConnected = false;
    this.notificationCount = 0;

    this.init();
  }

  init() {
    // Try WebSocket first, fallback to SSE
    if (this.supportsWebSocket()) {
      this.connectWebSocket();
    } else if (this.supportsSSE()) {
      this.connectSSE();
    } else {
      console.warn(
        "Neither WebSocket nor SSE supported. Notifications will not work.",
      );
    }

    // Set up periodic reconnection
    this.setupReconnection();
  }

  supportsWebSocket() {
    return typeof WebSocket !== "undefined";
  }

  supportsSSE() {
    return typeof EventSource !== "undefined";
  }

  connectWebSocket() {
    try {
      this.websocket = new WebSocket(this.getWebSocketUrl());

      this.websocket.onopen = (event) => {
        console.log("WebSocket connected");
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.options.onConnect(event);
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.websocket.onclose = (event) => {
        console.log("WebSocket disconnected");
        this.isConnected = false;
        this.options.onDisconnect(event);
        this.scheduleReconnect();
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.options.onError(error);
      };
    } catch (error) {
      console.error("Error creating WebSocket connection:", error);
      this.connectSSE(); // Fallback to SSE
    }
  }

  connectSSE() {
    try {
      this.eventSource = new EventSource(this.options.sseUrl);

      this.eventSource.onopen = (event) => {
        console.log("SSE connected");
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.options.onConnect(event);
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error("Error parsing SSE message:", error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error("SSE error:", error);
        this.options.onError(error);
        this.scheduleReconnect();
      };
    } catch (error) {
      console.error("Error creating SSE connection:", error);
    }
  }

  handleMessage(data) {
    switch (data.type) {
      case "notification":
        this.handleNotification(data.notification);
        break;
      case "notification_read":
        this.handleNotificationRead(data);
        break;
      case "notification_count":
        this.updateNotificationCount(data.count);
        break;
      case "connected":
        console.log("Connected to notification stream");
        break;
      case "heartbeat":
        // Keep connection alive
        break;
      case "error":
        console.error("Server error:", data.message);
        break;
      default:
        console.log("Unknown message type:", data.type);
    }
  }

  handleNotification(notification) {
    this.notificationCount++;
    this.updateNotificationCount(this.notificationCount);
    this.options.onNotification(notification);
  }

  handleNotificationRead(data) {
    // Update UI to show notification as read
    const notificationElement = document.querySelector(
      `[data-notification-id="${data.notification_id}"]`,
    );
    if (notificationElement) {
      notificationElement.classList.remove("unread");
      notificationElement.classList.add("read");
    }
  }

  updateNotificationCount(count) {
    this.notificationCount = count;

    // Update notification badge
    const badge = document.querySelector(".notification-badge");
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? "inline" : "none";
    }

    // Update page title
    if (count > 0) {
      document.title = `(${count}) ReferWell Direct`;
    } else {
      document.title = "ReferWell Direct";
    }
  }

  setupReconnection() {
    // Send ping every 30 seconds to keep connection alive
    setInterval(() => {
      if (this.isConnected) {
        this.ping();
      }
    }, 30000);
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect in ${this.options.reconnectInterval}ms (attempt ${this.reconnectAttempts})`,
      );

      setTimeout(() => {
        if (this.websocket) {
          this.connectWebSocket();
        } else if (this.eventSource) {
          this.connectSSE();
        }
      }, this.options.reconnectInterval);
    } else {
      console.error("Max reconnection attempts reached");
    }
  }

  ping() {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(
        JSON.stringify({
          type: "ping",
          timestamp: Date.now(),
        }),
      );
    }
  }

  markAsRead(notificationId) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(
        JSON.stringify({
          type: "mark_read",
          notification_id: notificationId,
        }),
      );
    } else {
      // Fallback to API call
      this.markAsReadAPI(notificationId);
    }
  }

  async markAsReadAPI(notificationId) {
    try {
      const response = await fetch(
        `/api/notifications/${notificationId}/mark_read/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": this.getCSRFToken(),
          },
        },
      );

      if (response.ok) {
        console.log("Notification marked as read via API");
      }
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  }

  getCSRFToken() {
    const token = document.querySelector("[name=csrfmiddlewaretoken]");
    return token ? token.value : "";
  }

  getWebSocketUrl() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    return `${protocol}//${host}${this.options.websocketUrl}`;
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    this.isConnected = false;
  }

  // Default handlers
  defaultNotificationHandler(notification) {
    console.log("New notification:", notification);

    // Show browser notification if permission granted
    if (Notification.permission === "granted") {
      new Notification(notification.title, {
        body: notification.message,
        icon: "/static/img/logo.png",
      });
    }
  }

  defaultErrorHandler(error) {
    console.error("Notification client error:", error);
  }

  defaultConnectHandler(event) {
    console.log("Notification client connected");
  }

  defaultDisconnectHandler(event) {
    console.log("Notification client disconnected");
  }
}

// Initialize notification client when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Request notification permission
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }

  // Initialize notification client
  window.notificationClient = new NotificationClient({
    onNotification: function (notification) {
      // Show notification in UI
      showNotificationInUI(notification);

      // Show browser notification
      if (Notification.permission === "granted") {
        new Notification(notification.title, {
          body: notification.message,
          icon: "/static/img/logo.png",
        });
      }
    },
  });
});

function showNotificationInUI(notification) {
  // Create notification element
  const notificationElement = document.createElement("div");
  notificationElement.className = "notification-toast";
  notificationElement.innerHTML = `
        <div class="notification-content">
            <h4>${notification.title}</h4>
            <p>${notification.message}</p>
            <div class="notification-actions">
                <button onclick="markNotificationAsRead('${notification.id}')" class="btn btn-sm btn-primary">Mark as Read</button>
                <button onclick="dismissNotification(this)" class="btn btn-sm btn-secondary">Dismiss</button>
            </div>
        </div>
    `;

  // Add to notification container
  let container = document.querySelector(".notification-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "notification-container";
    document.body.appendChild(container);
  }

  container.appendChild(notificationElement);

  // Auto-dismiss after 10 seconds
  setTimeout(() => {
    if (notificationElement.parentNode) {
      notificationElement.remove();
    }
  }, 10000);
}

function markNotificationAsRead(notificationId) {
  if (window.notificationClient) {
    window.notificationClient.markAsRead(notificationId);
  }
}

function dismissNotification(button) {
  button.closest(".notification-toast").remove();
}

// CSS for notification toasts
const notificationStyles = `
.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 400px;
}

.notification-toast {
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.notification-content h4 {
    margin: 0 0 8px 0;
    font-size: 16px;
    color: #0b0c0c;
}

.notification-content p {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #626a6e;
}

.notification-actions {
    display: flex;
    gap: 8px;
}

.notification-badge {
    background: #d4351c;
    color: #ffffff;
    border-radius: 50%;
    padding: 2px 6px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 5px;
}
`;

// Inject styles
const styleSheet = document.createElement("style");
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
