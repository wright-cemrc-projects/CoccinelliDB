import {Create, useForm, useSelect} from "@refinedev/antd";
import {Form, Input, DatePicker, Select, Table, Switch, Button} from "antd";
import {Facility, Instrument, Person, Project} from "@/src/type";
import {DeleteOutlined, PlusOutlined} from "@ant-design/icons";
import {useState} from "react";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone"

dayjs.extend(utc);
dayjs.extend(timezone);

export const InstrumentSessionCreate = () => {
    const { formProps, saveButtonProps } = useForm({});
    const [persons, setPersons] = useState<
        { person_id: number; onsite: boolean; role: string; remote_access_level: string }[]
    >([]);
    const addPerson = () => {
        setPersons([...persons, { person_id: 0, onsite: false, role: "", remote_access_level: "" }]);
    };

    const removePerson = (index: number) => {
        setPersons(persons.filter((_, i) => i !== index));
    };

    const updatePerson = (index: number, key: string, value: any) => {
        const updatedPersons = [...persons];
        updatedPersons[index] = { ...updatedPersons[index], [key]: value };
        setPersons(updatedPersons);
    };
    const { selectProps: facilitySelectProps } = useSelect({
        resource: "facilities",
        optionLabel: (item: Facility) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });
    const { selectProps: personSelectProps } = useSelect({
        resource: "persons",
        optionLabel: (item: Person) => `${item?.first_name} ${item?.last_name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "first_name",
                operator: "contains",
                value: value,
            },
            {
                field: "last_name",
                operator: "contains",
                value: value,
            },
        ],
    });
    const { selectProps: instrumentSelectProps } = useSelect({
        resource: "instruments",
        optionLabel: (item: Instrument) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });
    const { selectProps: projectSelectProps } = useSelect({
        resource: "projects",
        optionLabel: (item: Project) => `${item?.project_id}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "project_id",
                operator: "contains",
                value: value,
            },

        ],
    });

    const handleFormSubmit = (values: any) => {
        const payload = { ...values,
            start_date: values.start_date
                ? dayjs(values.start_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
            end_date: values.end_date
                ? dayjs(values.end_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
        }
        formProps.onFinish?.(payload);
    };

    return (
        <Create saveButtonProps={saveButtonProps}>
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit}>
            <Form.Item
                    label={"Start Date"}
                    name={["start_date"]}
                    rules={[
                        {
                            required: true, message: "Start Date is required"
                        },
                    ]}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"End Date"}
                    name={["end_date"]}
                    rules={[
                        {
                            required: true, message: "End Date is required"
                        },
                    ]}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }}  // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"Facility"}
                    name={["facility_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...facilitySelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Project"}
                    name={["project_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Select
                        {...projectSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Instrument"}
                    name={["instrument_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...instrumentSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item label="Session Participants" name={["persons"]}>
                    <Table dataSource={persons} rowKey="person_id" pagination={false} size="small">
                        <Table.Column
                            title="Person"
                            dataIndex="person_id"
                            render={(value, _, index) => (
                                <Select
                                    {...personSelectProps}
                                    value={value}
                                    onChange={(val) => updatePerson(index, "person_id", val)}
                                    style={{ width: "100%" }}
                                />
                            )}
                        />
                        <Table.Column
                            title="Onsite"
                            dataIndex="onsite"
                            render={(value, _, index) => (
                                <Switch checked={value} onChange={(val) => updatePerson(index, "onsite", val)} />
                            )}
                        />
                        <Table.Column
                            title="Role"
                            dataIndex="role"
                            render={(value, _, index) => (
                                <Select
                                    value={value}
                                    onChange={(selectedValue) => updatePerson(index, "role", selectedValue)}
                                    placeholder="Select a role"
                                    style={{ width: "100%" }}
                                    options={[
                                        { label: "Staff", value: "staff" },
                                        { label: "Trainee", value: "trainee" },
                                        { label: "Independent Operator", value: "operator" },
                                        { label: "Client", value: "client" },
                                        { label: "Observer", value: "observer" },
                                        { label: "Other", value: "other" },
                                    ]}
                                />
                            )}
                        />
                        <Table.Column
                            title="Hours"
                            dataIndex="Hours"
                            render={(value, _, index) => (
                                <input type="number" value={value} onChange={(v) => updatePerson(index, "hours", value)} />
                            )}
                        />
                        <Table.Column
                            title="Remote Access Level"
                            dataIndex="remote_access_level"
                            render={(value, _, index) => (
                                <Select
                                    value={value}
                                    onChange={(selectedValue) => updatePerson(index, "remote_access_level", selectedValue)}
                                    placeholder="Select remote access level"
                                    style={{ width: "100%" }}
                                    options={[
                                        { label: "No access", value: "no access" },
                                        { label: "Remote view", value: "remote view" },
                                        { label: "Remote control", value: "remote control" },
                                    ]}
                                />
                            )}
                        />
                        <Table.Column
                            title="Action"
                            render={(_, __, index) => (
                                <Button danger icon={<DeleteOutlined />} onClick={() => removePerson(index)} />
                            )}
                        />
                    </Table>
                    <Button type="dashed" icon={<PlusOutlined />} onClick={addPerson} style={{ marginTop: 10 }}>
                        Add Person
                    </Button>
                </Form.Item>
            </Form>
        </Create>
    );
};
