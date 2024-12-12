import { Space, Typography } from "antd";
import {UserTag} from "@/src/components/tags/user-tag";
import {Person} from "@/src/type";

type Props = {
    users?: Array<Person>
};

export const UsersHeader = ({ users = [] }: Props) => {
    if (users.length > 0) {
        return (
            <Space size={[0, 8]} wrap>
                {users.map((user) => (
                    <UserTag key={user.id} user={user} />
                ))}
            </Space>
        );
    }

    return <Typography.Link>Assign to users</Typography.Link>;
};