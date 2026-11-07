package workbench.jmm.l06;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.Objects;

public final class SettlementSlot {
    private static final VarHandle ITEM;
    static {
        try {
            ITEM = MethodHandles.lookup().findVarHandle(SettlementSlot.class, "item", Settlement.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private Settlement item;   // null means empty; every access below names its mode

    public boolean offer(Settlement s) {
        Objects.requireNonNull(s, "s");
        // acquire: pairs with the consumer's release of null, so the consumer is done with the old item
        if (ITEM.getAcquire(this) != null) return false;
        // release: the producer's plain writes to s's fields can't move after this store
        ITEM.setRelease(this, s);
        return true;
    }

    public Settlement poll() {
        // acquire: if we see s, we also see every write the producer made before releasing it
        Settlement s = (Settlement) ITEM.getAcquire(this);
        if (s != null) ITEM.setRelease(this, null);   // hand the empty slot back to the producer
        return s;
    }
}
