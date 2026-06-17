# Web DataShare: Data Review Meeting Visuals

This application is a comprehensive data visualization and review dashboard designed for tracking, analyzing, and presenting key health performance indicators. The landing page serves as the central "Summary Performance Dashboard," allowing stakeholders to instantly monitor program performance against established targets.

Web DataShare is an opensource alternative to Power-BI & Tableau with a Generative AI twist to it. This is a hobbyist project that is still under development, it's not yet fully ready for production deployment.

The complete deployment includes a chatbot (the front end works, but the backend is still work in progress, still not 100% working but getting there, the pipelines are working, just need to improve on their reliability) that is powered by Gemini, OpenAI (backup) and many others.

## Landing Page
### Key Interface Components
Comprehensive Filter Ribbon: The top section provides a robust set of dropdown filters to slice the data. Users can drill down by geographical hierarchy (County, Sub County, Ward, Facility), timeframes (Financial Year, Quarter, Month), and demographic categories (Gender, Coarse Age, Finer Age).

Sidebar Navigation: A structured, collapsible left-hand menu organizes the application into distinct programmatic areas. Users can easily navigate between the Summary Dashboard, Prevention Performance, PMTCT & Cervical Cancer, TB Case Finding, Care & Treatment, and Trend Graphs.

Performance Data Table: The main content area displays a detailed, responsive table comparing actual achievements against predefined goals.

Metrics Tracked: Lists specific programmatic health indicators (e.g., HTS_TST, TX_NEW, TX_CURR, TB_ART).

Target vs. Achievement: Clearly outlines the annual target, a pro-rated cumulative target (e.g., 6-month), and the actual cumulative achievement.

Color-Coded Status: Employs a visual threshold system to highlight performance percentages. A prominent legend (ranging from Red <60% to Dark Green >95%) makes it instantly clear which indicators are excelling and which require immediate attention.

AI Integration: Features a "Talk with Web - DataShare Agentic AI Chatbot" button in the upper right, indicating built-in conversational AI support for querying data or navigating the platform.

This layout is highly optimized for data review meetings, enabling quick, data-driven decision-making by visually surfacing performance gaps and successes.

## Agentic AI Assistant Interface

This component introduces a conversational, AI-driven interface that allows users to interact naturally with the system's underlying datasets. By integrating an agentic chatbot, the platform simplifies data discovery, enabling users to query complex health indicators using plain language rather than manually configuring filters.

### Key Interface Components

Interactive Chat Window: A clean, user-friendly messaging interface designed for continuous dialogue with the AI. Upon opening, it provides a welcoming prompt that includes examples of actionable, natural language queries (e.g., "Show me HTS_TST performance in Nyamira" or "What are the TX_NEW trends?").

Dynamic Model Selection: Located in the header panel, a dropdown menu allows developers or administrators to toggle between different backend language models. The current configuration shows "Local LLM (SGLang)," demonstrating the application's capability to run privacy-preserving, on-premise AI inference.

Natural Language Input: A straightforward text input field at the base of the window ("Type your data query here...") paired with a "Send" button, facilitating seamless submission of ad-hoc data requests.

This chat interface represents a shift from static reporting to dynamic, conversational data exploration, empowering stakeholders of all technical backgrounds to instantly retrieve the specific insights they need.
