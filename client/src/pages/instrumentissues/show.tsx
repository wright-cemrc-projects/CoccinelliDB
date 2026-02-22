import { Show, TextField } from "@refinedev/antd";
import { useShow } from "@refinedev/core";
import { Typography } from "antd";

const { Title } = Typography;

export const InstrumentIssueShow = () => {
    const { query } = useShow({});
    const { data, isLoading } = query;

    const record = data?.data;

    return (
        <Show isLoading={isLoading} headerProps={{ title: false }}>
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />

            <Title level={5}>{"Instrument ID"}</Title>
            <TextField value={record?.name} />

            <Title level={5}>{"Issue Title"}</Title>
            <TextField value={record?.issue_title} />

            <Title level={5}>{"Issue Description"}</Title>
            <TextField value={record?.issue_description} />

            <Title level={5}>{""}</Title>
            <TextField value={record?.model} />
        </Show>
    );
};