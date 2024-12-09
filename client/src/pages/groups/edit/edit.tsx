import { Edit, useForm } from "@refinedev/antd";
import { Form, Input } from "antd";
import {useState} from "react";

export const GroupEdit = () => {
    const { formProps, saveButtonProps } = useForm({});
    const [activeKey, setActiveKey] = useState<string | undefined>();

    return (
        <Edit saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item
                    label={"Name"}
                    name={["name"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>

            </Form>

        </Edit>
    );
};