import { Create, useForm, useSelect } from "@refinedev/antd";
import { Form, Input, Select } from "antd";
import { InstrumentSession, SessionGroup } from "@/src/type";

import dayjs from "dayjs";

const sessionLabel = (session: InstrumentSession) => {
    const range = session?.start_date
        ? `${dayjs(session.start_date).format("YYYY-MM-DD HH:mm")} – ${
              session.end_date ? dayjs(session.end_date).format("HH:mm") : "?"
          }`
        : "no dates";
    return `#${session?.id} · ${session?.instrument?.name ?? "?"} · ${range}`;
};

/** Link a set of existing sessions together as one block. */
export const SessionGroupCreate = () => {
    const { formProps, saveButtonProps } = useForm<SessionGroup>();

    const { selectProps: sessionSelectProps } = useSelect({
        resource: "instrumentsession",
        optionLabel: (item: InstrumentSession) => sessionLabel(item),
        optionValue: "id",
        onSearch: undefined,
    });

    return (
        <Create saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item
                    label={"Name"}
                    name={["name"]}
                    rules={[{ required: true, message: "Name is required" }]}
                >
                    <Input placeholder="e.g. Krios March 2–4 booking" />
                </Form.Item>
                <Form.Item label={"Notes"} name={["notes"]}>
                    <Input.TextArea rows={4} placeholder="What ties these sessions together..." />
                </Form.Item>
                <Form.Item label={"Linked Sessions"} name={["session_ids"]}>
                    <Select
                        {...sessionSelectProps}
                        mode="multiple"
                        allowClear
                        placeholder="Select the sessions in this block"
                        style={{ width: "100%" }}
                    />
                </Form.Item>
            </Form>
        </Create>
    );
};
