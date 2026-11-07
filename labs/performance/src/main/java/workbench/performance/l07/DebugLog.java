package workbench.performance.l07;

/** The small part of a logging facade this lab needs. */
public interface DebugLog {
    boolean isDebugEnabled();

    void debug(String message);
}
