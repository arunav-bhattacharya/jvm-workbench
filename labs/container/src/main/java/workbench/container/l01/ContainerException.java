package workbench.container.l01;

/** Anything the container can't wire: a cycle, a missing component, an ambiguous constructor. */
public class ContainerException extends RuntimeException {
    public ContainerException(String message) {
        super(message);
    }

    public ContainerException(String message, Throwable cause) {
        super(message, cause);
    }
}
