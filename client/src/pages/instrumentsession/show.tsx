import { Show, TextField } from "@refinedev/antd";
import { useShow } from "@refinedev/core";
import { Typography } from "antd";

const { Title } = Typography;

export const InstrumentSessionShow = () => {
    const { query } = useShow({});
    const { data, isLoading } = query;

    const record = data?.data;

    return (
        <Show isLoading={isLoading} headerProps={{ title: false }}>
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />
            <Title level={5}>{"Start Time"}</Title>
            <TextField value={record?.start_date} />
            <Title level={5}>{"End Time"}</Title>
            <TextField value={record?.end_date} />
            <Title level={5}>{"End of Session Notes"}</Title>
            <TextField value={record?.notes || "—"} />
        </Show>
    );
};

