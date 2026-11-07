package workbench.jmm.l06;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.Objects;

public final class KillSwitch {
    private static final VarHandle REASON;
    static {
        try {
            REASON = MethodHandles.lookup().findVarHandle(KillSwitch.class, "reason", String.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private String reason;   // null until tripped; every access goes through REASON

    public boolean trip(String why) {
        Objects.requireNonNull(why, "why");
        // one atomic step with volatile semantics: exactly one caller sees null and wins
        return REASON.compareAndSet(this, null, why);
    }

    public boolean isTripped() {
        // acquire: re-read on every call (the JIT can't hoist it), and ordered after the winning write
        return REASON.getAcquire(this) != null;
    }

    public String reason() {
        return (String) REASON.getAcquire(this);
    }
}
