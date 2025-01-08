import { Show, TextField } from "@refinedev/antd";
import { useShow } from "@refinedev/core";
import { Typography } from "antd";

const { Title } = Typography;

export const ProjectShow = () => {
    const { queryResult } = useShow({});
    const { data, isLoading } = queryResult;

    const record = data?.data;

    return (
        <Show isLoading={isLoading}>
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />

            <Title level={5}>{"Project_ID"}</Title>
            <TextField value={record?.project_id} />

            <Title level={5}>{"Facility_ID"}</Title>
            <TextField value={record?.facility_id} />
        </Show>
    );
};