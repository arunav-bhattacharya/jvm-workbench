package workbench.startup.l03;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Turns a message into an event object by class name, and reads it back by accessor name, the
 * way JSON and Kafka serializers do. The class name comes from the message, so the native-image
 * analysis cannot see which class or members are used. Don't change this class.
 */
public final class EventDecoder {
    /** The accessors {@link #describe} calls, by name. */
    public static final List<String> ACCESSORS = List.of("paymentId", "currency", "amountMinor");

    private EventDecoder() {
    }

    /** Creates the event class named in the message header through its (String, String, long) constructor. */
    public static Object decode(String typeName, String paymentId, String currency, long amountMinor)
            throws ReflectiveOperationException {
        Class<?> type = Class.forName(typeName);                       // a name from data, not a constant
        return type.getConstructor(String.class, String.class, long.class)
                .newInstance(paymentId, currency, amountMinor);
    }

    /** Reads the event's fields through its accessor methods, looked up by name. */
    public static Map<String, Object> describe(Object event) throws ReflectiveOperationException {
        Map<String, Object> out = new LinkedHashMap<>();
        for (String accessor : ACCESSORS) {
            out.put(accessor, event.getClass().getMethod(accessor).invoke(event));
        }
        return out;
    }
}
