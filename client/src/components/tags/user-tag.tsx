import { Space, Tag } from "antd";

import {Person} from "../../type";

type Props = {
    user: Person;
};

export const UserTag = ({ user }: Props) => {
    return (
        <Tag
            key={user.id}
            style={{
                padding: 2,
                paddingRight: 8,
                borderRadius: 24,
                lineHeight: "unset",
                marginRight: "unset",
            }}
        >
            <Space size={4}>
                {user?.first_name} {user?.last_name}
            </Space>
        </Tag>
    );
};
