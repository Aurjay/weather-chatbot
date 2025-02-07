/**
 * Copyright (c) 2024–2025, Daily
 * SPDX-License-Identifier: BSD 2-Clause License
 */

/**
 * Frontend Client Implementation
 * This client interacts with the FastAPI server (chatbot & weather API).
 */

class ChatbotClient {
  constructor() {
    // Initialize client state
    this.setupDOMElements();
    this.setupEventListeners();
  }

  /**
   * Set up references to DOM elements and create necessary UI elements
   */
  setupDOMElements() {
    this.connectBtn = document.getElementById('connect-btn');
    this.disconnectBtn = document.getElementById('disconnect-btn');
    this.statusSpan = document.getElementById('connection-status');
    this.debugLog = document.getElementById('debug-log');
    this.chatInput = document.getElementById('chat-input');
    this.chatSubmitBtn = document.getElementById('chat-submit-btn');
    this.weatherContainer = document.getElementById('weather-container');
  }

  /**
   * Set up event listeners for connect/disconnect buttons and chat submission
   */
  setupEventListeners() {
    this.connectBtn.addEventListener('click', () => this.connect());
    this.disconnectBtn.addEventListener('click', () => this.disconnect());
    this.chatSubmitBtn.addEventListener('click', () => this.handleChatSubmit());
  }

  /**
   * Add a timestamped message to the debug log
   */
  log(message) {
    const entry = document.createElement('div');
    entry.textContent = `${new Date().toISOString()} - ${message}`;
    this.debugLog.appendChild(entry);
    this.debugLog.scrollTop = this.debugLog.scrollHeight;
    console.log(message);
  }

  /**
   * Update the connection status display
   */
  updateStatus(status) {
    this.statusSpan.textContent = status;
    this.log(`Status: ${status}`);
  }

  /**
   * Handle chat submission
   */
  async handleChatSubmit() {
    const userMessage = this.chatInput.value.trim();
    if (userMessage === '') return;

    this.log(`User: ${userMessage}`);

    // Send the user message to the backend
    try {
      const response = await fetch('http://localhost:7860/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await response.json();
      this.displayChatResponse(data.response);
    } catch (error) {
      this.log(`Error: ${error.message}`);
    }

    this.chatInput.value = '';  // Clear input after submission
  }

  /**
   * Display the bot's response
   */
  displayChatResponse(response) {
    const entry = document.createElement('div');
    entry.style.color = '#4CAF50'; // Green for bot
    entry.textContent = `Bot: ${response}`;
    this.debugLog.appendChild(entry);
    this.debugLog.scrollTop = this.debugLog.scrollHeight;
  }

  /**
   * Connect to the bot (Mock - this can be expanded as needed)
   */
  connect() {
    this.updateStatus('Connected');
    this.connectBtn.disabled = true;
    this.disconnectBtn.disabled = false;
    this.log('Client connected');
  }

  /**
   * Disconnect from the bot (Mock)
   */
  disconnect() {
    this.updateStatus('Disconnected');
    this.connectBtn.disabled = false;
    this.disconnectBtn.disabled = true;
    this.log('Client disconnected');
  }

  /**
   * Fetch weather information based on city
   */
  async getWeather(city) {
    try {
      const response = await fetch(`http://localhost:7860/weather?city=${city}`);
      const data = await response.json();

      if (data.city) {
        this.displayWeather(data);
      } else {
        this.weatherContainer.innerHTML = '<p>Could not retrieve weather data.</p>';
      }
    } catch (error) {
      this.weatherContainer.innerHTML = '<p>Error fetching weather data.</p>';
    }
  }

  /**
   * Display weather data
   */
  displayWeather(data) {
    this.weatherContainer.innerHTML = `
      <h3>Weather in ${data.city}</h3>
      <p>Temperature: ${data.temperature}°C</p>
      <p>Condition: ${data.condition}</p>
      <p>Humidity: ${data.humidity}%</p>
      <p>Wind Speed: ${data.wind_speed} kph</p>
    `;
  }
}

// Initialize the client when the page loads
window.addEventListener('DOMContentLoaded', () => {
  new ChatbotClient();
});
