import { Create, useForm } from "@refinedev/antd";
import { Form, Input } from "antd";

export const ProjectCreate = () => {
    const { formProps, saveButtonProps } = useForm({});

    return (
        <Create saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical">
                <Form.Item
                    label={"Project_ID"}
                    name={["project_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>
                <Form.Item
                    label={"Facility_ID"}
                    name={["facility_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Input />
                </Form.Item>
            </Form>
        </Create>
    );
};