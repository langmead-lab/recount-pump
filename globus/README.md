The client ID in the `client_id.txt` file corresponds to the "SDK Tutorial Project" "app."   There's also a `recount-pump` app.  Both can be [seen here](https://auth.globus.org/v2/web/developers).

## Glossary

* _client id_ -- something a registered application gets
    * [Register app](https://docs.globus.org/api/auth/developer-guide/#register-app)
    * [Developers site](https://developers.globus.org)
* _endpoint_ -- something that can send or receive data via Globus
* _oauth2_ -- autorization API
    * [OAuth 2.0 site](https://oauth.net/2/)
* _Globus Auth_ -- XYZ
* _Client definition_ -- something you register with Globus Auth
* _Native app authentication_ -- OAuth2 Native App Authentication.  "Application" is the term used in OAuth2 speak.  "Application" is at the center of the process.  Process begins with (as-yet-unauthenticated) user interacting with the application.  App asks user to authenticate and user passes app a token.  App then contacts authorization server and trades token for authorization.  App then contacts resource server and passes authorization.
* _Authorization Grant_ -- the mechanism whereby authorization is granted to the application.  Could be
    * Information gleaned from [DigitalOcean's oath2 tutorial](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2)
    * _Authorization Code_ -- where the user has to follow a URL to complete the grant.
    * __
    * _Resource Owner Password Credentials_, where "user provides their service credentials (username and password) directly to the application, which uses the credentials to obtain an access token from the service."
* _Transfer Client_ -- XYZ
* _Access Token_ -- XYZ
* _Refresh Token_ -- XYZ

## SDK glossary

* `AccessTokenAuthorizer`
    * From [API documentation](https://globus-sdk-python.readthedocs.io/en/stable/examples/authorization/?highlight=AccessTokenAuthorizer#access-token-authorization-on-authclient-and-transferclient)
        * Access Tokens are used to directly authenticate calls against Globus APIs, and are _limited-lifetime_ credentials
        * You have distinct Access Tokens for each Globus service which you want to access.
* `RefreshTokenAuthorizer`
    * From [API documentation](https://globus-sdk-python.readthedocs.io/en/stable/examples/authorization/?highlight=AccessTokenAuthorizer#refresh-token-authorization-on-authclient-and-transferclient)
        * Refresh Tokens are long-lived credentials used to get new Access Tokens whenever they near expiration. 
        * Re-upping credentials is an operation that _requires having client credentials for Globus Auth_.
* `ConfidentialAppAuthClient`
* `NativeAppAuthClient`
    * From [API documentation](https://globus-sdk-python.readthedocs.io/en/stable/examples/native_app/#native-app-login)
        * The goal here is to have a user authenticate in Globus Auth, and for the SDK to procure tokens which may be used to authenticate SDK calls against various services for that user.
        * In order to complete an OAuth2 flow to get tokens, you must have a client definition registered with Globus Auth.
* `TransferClient`


I think this is what we want to do: https://globus-sdk-python.readthedocs.io/en/stable/examples/client_credentials/

Do I have any code that does this already?