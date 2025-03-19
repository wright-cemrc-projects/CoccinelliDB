import {
    DeleteButton,
    EditButton,
    List, Show,
    ShowButton,
    useTable,
} from "@refinedev/antd";
import {BaseRecord, useList} from "@refinedev/core";
import {Badge, BadgeProps, Calendar} from "antd";
import {InstrumentSession} from "@/src/type";
import dayjs from "dayjs";

export const InstrumentSessionShow = () => {
    const { data } = useList<InstrumentSession>({
        resource: "instrumentsession",
    });
    const panelChange = () => {
        console.log("panel change")
    }

    const cellRender = (value: dayjs.Dayjs) => {
        const listData = data?.data?.filter((p) =>
            dayjs(p.start_date).isSame(value, "day"),
        );
        return (
            <ul className="events">
                {listData?.map((item) => (
                    <li key={item.id}>
                        {item.id}
                    </li>
                ))}
            </ul>
        );
    }

    return (
        <Show headerProps={{ extra: null }}>
            <Calendar
                onPanelChange={panelChange}
                cellRender={cellRender}
            />
        </Show>
    );
};

