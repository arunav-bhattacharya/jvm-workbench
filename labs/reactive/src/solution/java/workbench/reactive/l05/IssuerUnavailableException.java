package workbench.reactive.l05;

/** The issuer is overloaded or briefly down: a later attempt may succeed. */
public class IssuerUnavailableException extends RuntimeException {
    public IssuerUnavailableException(String message) {
        super(message);
    }
}
