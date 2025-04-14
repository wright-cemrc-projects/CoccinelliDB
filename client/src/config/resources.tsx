import type { IResourceItem } from "@refinedev/core";
import {DashboardOutlined, GroupOutlined, UserOutlined, ProjectOutlined, CalendarOutlined, AlertOutlined} from "@ant-design/icons";


export const resources: IResourceItem[] = [
    {
      name: "roles"
    },
    {
      name: "dashboard",
      list: "/",
      meta: {
          label: "Dashboard",
          icon: <DashboardOutlined />,
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

];

const roleAccessMap: Record<string, string[]> = {
    admin: [], // access to everything
    editor: ["roles", "facilities", "groups", "persons"], // deny user related routes
    user: [
        "roles",
        "facilities",
        "groups",
        "persons",
        "projects",
        "instruments",
        "instrumentsession",
        "instrumentissues"
    ], // allow only dashboard
};

export const filterResourcesByRoles = (roles: string[]): IResourceItem[] => {
    roles = roles.map((e) => e.toLowerCase());
    if (roles.includes("admin")) {
        return resources; // full access
    }

    // Collect denied resources from all roles (union)
    const denied = new Set<string>();
    roles.forEach(role => {
        roleAccessMap[role]?.forEach(resource => denied.add(resource));
    });
    console.log(denied);
    return resources.filter(resource => !denied.has(resource.name));
};