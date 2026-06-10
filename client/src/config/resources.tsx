import type { IResourceItem } from "@refinedev/core";
import {
    DashboardOutlined,
    GroupOutlined,
    UserOutlined,
    ProjectOutlined,
    CalendarOutlined,
    AlertOutlined,
    UsergroupAddOutlined,
    AuditOutlined,
} from "@ant-design/icons";


export const resources: IResourceItem[] = [

    {
      name: "dashboard",
      list: "/",
      meta: {
          label: "Dashboard",
          icon: <DashboardOutlined />,
      }
    },
    {
        name: "roles",
        list: "/roles",
        create: "/roles/create",
        edit: "/roles/edit/:id",
        show: "/roles/show/:id",
        meta: {
            label: "Roles",
            canDelete: true,
            icon: <UsergroupAddOutlined />
        }
    },
    {
        name: "facilities",
        list: "/facilities",
        create: "/facilities/create",
        edit: "/facilities/edit/:id",
        show: "/facilities/show/:id",
        meta: {
            label: "Facilities",
            canDelete: true,
            icon: <ProjectOutlined />
        }
    },
    {
        name: "groups",
        list: "/groups",
        create: "/groups/create",
        edit: "/groups/edit/:id",
        show: "/groups/show/:id",
        meta: {
            label: "Groups",
            canDelete: true,
            icon: <GroupOutlined />,
        }
    },
    {
        name: "persons",
        list: "/persons",
        create: "/persons/create",
        edit: "/persons/edit/:id",
        show: "/persons/show/:id",
        meta: {
            label: "Persons",
            canDelete: true,
            icon: <UserOutlined />
        }
    },
    {
        name: "projects",
        list: "/projects",
        create: "/projects/create",
        edit: "/projects/edit/:id",
        show: "/projects/show/:id",
        meta: {
            label: "Projects",
            canDelete: true,
            icon: <ProjectOutlined />
        }
    },
    {
        name: "instruments",
        list: "/instruments",
        create: "/instruments/create",
        edit: "/instruments/edit/:id",
        show: "/instruments/show/:id",
        meta: {
            label: "Instruments",
            canDelete: true,
            icon: <ProjectOutlined />
        }
    },
    {
        name: "instrumentsession",
        list: "/instrumentsession",
        create: "/instrumentsession/create",
        edit: "/instrumentsession/edit/:id",
        show: "/instrumentsession/show/:id",
        meta: {
            label: "Instrument Sessions",
            canDelete: true,
            icon: <CalendarOutlined />
        }
    },
    {
        name: "instrumentissues",
        list: "/instrumentissues",
        create: "/instrumentissues/create",
        edit: "/instrumentissues/edit/:id",
        show: "/instrumentissues/show/:id",
        meta: {
            label: "Instrument Issues",
            canDelete: true,
            icon: <AlertOutlined />
        }
    },
    {
        name: "collection",
        list: "/collection",
        show: "/collection/show/:id",
        meta: {
            label: "Collections",
            icon: <ProjectOutlined />
        }
    },
    {
        name: "remotelogs",
        list: "/remotelogs",
        meta: {
            label: "Remote Access Logs",
            icon: <AuditOutlined />
        }
    },

];

// Resources each role is allowed to access (admin = all, use [] as sentinel)
const roleAccessMap: Record<string, string[]> = {
    admin:  [], // sentinel: allow everything
    editor: ["dashboard", "projects", "instruments", "instrumentsession", "instrumentissues", "collection"],
    user:   ["dashboard", "projects", "instrumentsession"],
};

// Resources each role can only view (list + show) — no create, edit, or delete.
// Admin and Editor always get full write access regardless of this map.
const readOnlyAccessMap: Record<string, string[]> = {
    user: ["projects", "instrumentsession"],
};

function stripWriteAccess(resource: IResourceItem): IResourceItem {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { create, edit, ...rest } = resource;
    return { ...rest, meta: { ...rest.meta, canDelete: false } };
}

export const filterResourcesByRoles = (roles: string[]): IResourceItem[] => {
    if (roles.length === 0) {
        return resources.filter(resource => resource.name === "dashboard");
    }
    roles = roles.map((e) => e.toLowerCase());
    if (roles.includes("admin")) {
        return resources; // full access to all resources
    }

    // Collect all allowed resource names (union across all of the user's roles)
    const allowed = new Set<string>();
    roles.forEach(role => {
        roleAccessMap[role]?.forEach(resource => allowed.add(resource));
    });

    const filtered = resources.filter(resource => allowed.has(resource.name));

    // Apply read-only restrictions for roles that have them,
    // unless the user also holds a role with full write access (editor/admin).
    const hasWriteAccess = roles.includes("editor");
    if (hasWriteAccess) {
        return filtered;
    }

    // Collect read-only resource names across all of the user's roles
    const readOnly = new Set<string>();
    roles.forEach(role => {
        readOnlyAccessMap[role]?.forEach(resource => readOnly.add(resource));
    });

    return filtered.map(resource =>
        readOnly.has(resource.name) ? stripWriteAccess(resource) : resource
    );
};