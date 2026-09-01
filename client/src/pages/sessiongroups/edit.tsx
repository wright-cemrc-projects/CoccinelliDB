import { Edit, useForm, useSelect } from "@refinedev/antd";
import { Form, Input, Select } from "antd";
import { useEffect } from "react";
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

/** Rename a block of linked sessions and choose which sessions belong to it. */
export const SessionGroupEdit = () => {
    const { formProps, saveButtonProps, queryResult } = useForm<SessionGroup>({
        mutationMode: "pessimistic",
    });

    const { selectProps: sessionSelectProps } = useSelect({
        resource: "instrumentsession",
        optionLabel: (item: InstrumentSession) => sessionLabel(item),
        optionValue: "id",
        onSearch: undefined,
    });

    // Membership arrives as nested session objects; the API takes a list of ids.
    useEffect(() => {
        const sessions = queryResult?.data?.data?.sessions;
        if (sessions) {
            formProps.form?.setFieldsValue({ session_ids: sessions.map((s) => s.id) });
        }
    }, [queryResult?.data]);

    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item label={"Name"} name={["name"]}>
                    <Input placeholder="e.g. Krios March 2–4 booking" />
                </Form.Item>
                <Form.Item label={"Notes"} name={["notes"]}>
                    <Input.TextArea rows={4} placeholder="What ties these sessions together..." />
                </Form.Item>
                <Form.Item
                    label={"Linked Sessions"}
                    name={["session_ids"]}
                    help="Sessions removed here are unlinked from the group, not deleted."
                >
                    <Select
                        {...sessionSelectProps}
                        mode="multiple"
                        allowClear
                        placeholder="Select the sessions in this block"
                        style={{ width: "100%" }}
                    />
                </Form.Item>
            </Form>
        </Edit>
    );
};
