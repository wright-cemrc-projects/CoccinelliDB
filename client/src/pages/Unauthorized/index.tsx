export const Unauthorized = () => {
    return (
        <div style={{ textAlign: "center", padding: "50px" }}>
            <h1>Unauthorized Access</h1>
            <p>You do not have permission to access this application.</p>
            <a href="/">Go Back to Home</a>
        </div>
    );
};

export default Unauthorized;