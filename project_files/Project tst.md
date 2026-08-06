# Full Version in English 

---

## Detailed Specifications Document

## Project: GarderieNova – Comprehensive Educational Daycare Management Platform

---

## 1\. Project Objective

**Develop a modular, secure, and scalable web application designed for educational daycares in New Brunswick. The platform will be enhanced with innovative features tailored to the specific needs of directors, educators, administrative assistants, and parents. The goal is to optimize administrative management, educational documentation, family engagement, and legal compliance.**

---

## 2\. Main Features

## 2.1 Child Management (Profiles)

* **Create detailed profiles for each child (general information, parent contacts, two emergency contacts).**  
* **Track group change history and automatic educator assignment.**  
* **Age progression tracking with notifications 15 days before a group change.**  
* **Secure import/export of child records during daycare transfers (send/receive between centers).**  
* **Online registration and consent forms for parents (FR/EN).**

## 2.2 Waitlist Management

* **Module for managing pre-registrations and waitlists by age group.**  
* **Automatic notifications to parents when a spot becomes available.**  
* **Option to add notes or priorities (siblings, special situations).**

## 2.3 Real-time Attendance

* **Real-time check-in managed by each educator for their group.**  
* **Status options: Present, Absent, Left.**  
* **Global dashboard updated instantly.**  
* **Absence management and automatic notifications to parents.**

## 2.4 Legal Ratios by Department (New Brunswick Regulations)

* **Under 24 months:**  
  * **Ratio 1:3 (1 educator for 3 children)**  
  *   
  * **⌉**  
* **Ages 2–4:**  
  * **Age 2: 1:5 → 200**  
  *   
  * **⌈**  
  * **1050**  
  * **total values**  
  * **⌉**  
* **After-school (5+ years):**  
  *   
  * **15**  
  * **number of present children**  
  * **⌉**  
* **Department dashboards:**  
  * **Display of total present, cumulative value, required educators.**  
  * **Immediate visual alert if the legal ratio is exceeded.**  
  * **Global dashboard consolidating all department data for an overall view and efficient management.**  
  * **Historical ratio data for audits.**

## 2.5 Daily Activity Report – Under 24 Months

* **A form displaying the five days of the week for each child in the group.**  
* **The educator completes this report daily for each child.**  
* **Parents have secure access to view these reports.**  
* **Weekly history of reports is maintained, allowing tracking of each child’s development.**  
* **Educators or directors can download these reports individually or in bulk.**

## 2.6 Activity Reports (Full Module)

* **Comprehensive activity report creation (activity name, date, age group, participation, category, objectives, materials, instructions, observations).**  
* **Customizable, pre-filled templates.**  
* **Editable preview and styled PDF export (jsPDF).**  
* **Categorization of activities (intellectual, motor, social, creative, etc.).**  
* **Participation statistics for each child.**

## 2.7 Observations & Portfolios

* **Add multimedia observations (text, photos, videos).**  
* **Direct link to curriculum goals.**  
* **Individual portfolios accessible to parents.**  
* **Evolution timeline for each child.**

## 2.8 Curriculum Planning

* **Daily/weekly planning of educational activities.**  
* **Visual, collaborative calendar interface.**  
* **Direct links to educational goals and achievement tracking.**  
* **Centralized planning templates (for multi-site management).**

## 2.9 Internal Messaging & Notifications

* **Secure messaging system between educators, management, and parents.**  
* **Internal and email notifications (absences, incidents, reminders, etc.).**  
* **Network-wide messaging for multi-site operations (management ↔ families/teams).**  
* **Communication history.**

## 2.10 Digital Incident Report Signatures

* **Digital form with three signature steps: educator → parent → director.**  
* **Visual progress bar.**  
* **PDF export available only after all signatures are complete.**  
* **Secure archiving of reports.**

## 2.11 User Roles and Account Management

* **Roles: director, administrative assistant, educators, parents.**  
* **Account creation and management by the director.**  
* **Email invitations, secure verification, and activation.**  
* **Data access strictly limited by user role.**  
* **Automatic screen lock/unlock module on the ratios dashboard to prevent accidental touches, with easy activation/deactivation by authorized users.**

## 2.12 Fire Alarm Module

* **“Fire Alarm” function accessible on the educator dashboard.**  
* **Instant display of the list of children present in the group.**  
* **After evacuation, the educator takes attendance outside via the app to confirm each child’s safety.**  
* **Automatic archiving of the post-evacuation attendance report, accessible to management.**

## 2.13 Multi-site Tools and Centralization

* **Management of multiple centers with network-wide reporting and messaging.**  
* **Custom branding per site.**  
* **Centralized access control.**  
* **Shared planning templates and curriculums.**

## 2.14 Analytics and Continuous Improvement Tools

* **Analytical dashboard (attendance, ratios, activities, incidents, parental satisfaction).**  
* **Feedback tools for families and teams.**  
* **Export of statistics for audits and quality improvement.**

## 2.15 Professional Growth and Community of Practice (Optional)

* **Self-assessment and continuing education modules for educators.**  
* **Internal forums for sharing best practices.**  
* **Professional development tracking.**

---

## 3\. Technical Specifications

* **Backend: Django 5 / Python 3.11+**  
* **Frontend: React \+ Tailwind CSS**  
* **Database: PostgreSQL**  
* **PDF Generation: jsPDF**  
* **Authentication: JWT \+ email verification \+ screen lock**  
* **Notifications: Toast \+ transactional emails**  
* **Deployment: Docker, configuration files included**  
* **Multilingual: FR (default), EN ready**  
* **GDPR: Full compliance, encryption of sensitive data**

---

## 4\. Non-Functional Requirements

* **Responsive application (mobile/tablet/desktop)**  
* **Modern, intuitive interface adapted to all user roles**  
* **User activity logging**  
* **Enhanced security (encryption, restricted access, logs)**  
* **Optimized performance for multi-site management**

---

## 5\. Deliverables

* **Documented source code**  
* **Database schema**  
* **Full API documentation**  
* **Functional interfaces per role**  
* **PDF user guide**  
* **Docker deployment files**

---

## 6\. Validation Criteria

* **All functionalities tested and validated**  
* **No blocking bugs**  
* **Real-time ratio calculations and alerts**  
* **Fully operational digital incident report signature process**  
* **Customizable and exportable activity reports**  
* **Secure, role-based data access**  
* **Functional import/export of child records during transfers**

---

## 7\. Innovations and Creative Suggestions

* **Quick integration module for new centers (bulk data import).**  
* **AI assistant for personalized educational recommendations based on group profiles.**  
* **Digital health record module (vaccinations, allergies, medical follow-up) accessible to parents and educators.**  
* **Instant survey tool to collect family feedback on activities or satisfaction.**  
* **Companion mobile app (push notifications, quick check-in, instant messaging).**  
* **Interactive timelines for attendance and incident history.**  
* **Recognition badges for educators (gamification, internal recognition).**  
* **Automatic export of regulatory data for inspections or audits.**