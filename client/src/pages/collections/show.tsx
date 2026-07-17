import { Show, TextField } from "@refinedev/antd";
import { useNavigation, useShow } from "@refinedev/core";
import { Typography } from "antd";
import { Collection } from "@/src/type";

const { Title, Link } = Typography;

export const CollectionShow = () => {
    const { query } = useShow<Collection>({});
    const { data, isLoading } = query;
    const { show } = useNavigation();

    const record = data?.data;

    return (
        <Show isLoading={isLoading}>
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />

            <Title level={5}>{"Type"}</Title>
            <TextField value={record?.collection_type ?? "—"} />

            <Title level={5}>{"Data Location"}</Title>
            <TextField value={record?.data_location ?? "—"} />

            <Title level={5}>{"Start"}</Title>
            <TextField value={record?.start_date ? new Date(record.start_date).toLocaleString() : "—"} />

            <Title level={5}>{"End"}</Title>
            <TextField value={record?.end_date ? new Date(record.end_date).toLocaleString() : "—"} />

            <Title level={5}>{"Image Count"}</Title>
            <TextField value={record?.total_image_count ?? "—"} />

            <Title level={5}>{"Instrument Session"}</Title>
            {record?.instrument_session_id ? (
                <Link onClick={() => show("instrumentsession", record.instrument_session_id)}>
                    Session #{record.instrument_session_id}
                </Link>
            ) : (
                "—"
            )}
        </Show>
    );
};
