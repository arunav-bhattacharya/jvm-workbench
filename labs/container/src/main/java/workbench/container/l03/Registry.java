package workbench.container.l03;

import java.util.List;
import java.util.concurrent.Callable;

/** What callers need from a container: the reflective {@link Container} and a generated registry both provide it. */
public interface Registry {
    <T> T get(Class<T> type);

    /** Every component, each after everything it depends on. */
    List<Class<?>> creationOrder();

    /** Where @Timed records its calls. */
    CallLog callLog();

    /**
     * For generated code: runs a constructor that declares checked exceptions, which a static
     * initializer may not throw, and wraps them the way the reflective container does.
     */
    static <T> T construct(String component, Callable<T> constructor) {
        try {
            return constructor.call();
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new ContainerException("constructor of " + component + " failed", e);
        }
    }
}
