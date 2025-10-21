---
mode: agent
---
2 frontend solutions one is admin and the other is customer. The admin frontend is used to manage tenants, users, and other administrative tasks, while the customer frontend is used by end-users to interact with the system.
Both frontends share some common components, such as logo upload functionality, but they may have different implementations or additional features tailored to their specific use cases.
the admin context is only the tenant administration interface, while the customer context is the end-user interface.
The admin frontend is used by saas provider to manage tenants, users, and other administrative tasks, while the customer frontend is used by end-users to interact with the system.

folders admin and customer have a folder api and frontend subfolders, the api subfolder contains the backend code, while the frontend subfolder contains the user interface code.
shared folder has 2 subfolders, the SmartOpsPortal.Shared is for shared code between the admin and customer backends, while the smartops-portal-controls is for shared UI components.