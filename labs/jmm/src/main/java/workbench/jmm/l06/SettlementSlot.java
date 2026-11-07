package workbench.jmm.l06;

import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;

/**
 * A one-item mailbox between exactly one producer thread and exactly one consumer thread.
 * The producer fills in a {@link Settlement} with plain writes, then offers it. The consumer polls it.
 *
 * <p>Write {@link #offer} and {@link #poll} with {@link #ITEM}, using acquire reads and release writes,
 * so the consumer always sees the settlement's fields as the producer wrote them. Don't use
 * synchronized and don't make the field volatile: the memory mode goes on each access.
 */
public final class SettlementSlot {
    // Given: a VarHandle for the item field below. KillSwitch needs one like it.
    private static final VarHandle ITEM;
    static {
        try {
            ITEM = MethodHandles.lookup().findVarHandle(SettlementSlot.class, "item", Settlement.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private Settlement item;   // null means empty. A plain field: reach it only through ITEM.

    /** Producer only. Puts {@code s} into an empty slot and returns true, or returns false if the slot is still full. */
    public boolean offer(Settlement s) {
        throw new UnsupportedOperationException("TODO: if the slot is empty, release s into it");
    }

    /** Consumer only. Takes the settlement out of the slot, or returns null if the slot is empty. */
    public Settlement poll() {
        throw new UnsupportedOperationException("TODO: acquire the item; if there is one, release null back");
    }
}
