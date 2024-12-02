import { Show, TextField } from "@refinedev/antd";
import { useShow } from "@refinedev/core";
import { Typography } from "antd";

const { Title } = Typography;

export const PersonShow = () => {
    const { queryResult } = useShow({});
    const { data, isLoading } = queryResult;

    const record = data?.data;

    return (
        <Show isLoading={isLoading}>
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />

            <Title level={5}>{"Full Name"}</Title>
            <TextField value={record?.first_name + " " + record?.last_name} />

            <Title level={5}>{"Net ID"}</Title>
            <TextField value={record?.net_id}/>
            
            <Title level={5}>{"Email"}</Title>
            <TextField value={record?.email}/>
            
            <Title level={5}>{"Start Date"}</Title>
            <TextField value={!record?.start_date ? "None" : record?.start_date}></TextField>
            
            <Title level={5}>{"End Date"}</Title>
            <TextField value={!record?.end_date ? "None" : record?.end_date}></TextField>
            
            <Title level={5}>{"Organization"}</Title>
            <TextField value={!record?.organization ? "None" : record?.organization}></TextField>
            
            <Title level={5}>{"Address1"}</Title>
            <TextField value={!record?.address1 ? "None" : record?.address1}></TextField>
            
            <Title level={5}>{"Address2"}</Title>
            <TextField value={!record?.address2 ? "None" : record?.address2}></TextField>
            
            <Title level={5}>{"State"}</Title>
            <TextField value={!record?.state ? "None" : record?.state}></TextField>
            
            <Title level={5}>{"Country"}</Title>
            <TextField value={!record?.country ? "None" : record?.country}></TextField>
            
            <Title level={5}>{"Telephone"}</Title>
            <TextField value={!record?.telephone ? "None" : record?.telephone}></TextField>
        </Show>
    );
};