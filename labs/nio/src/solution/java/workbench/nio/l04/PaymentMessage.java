package workbench.nio.l04;

/**
 * One message on the payment link. Wire format, big-endian:
 * <pre>
 * +----------------+-----------+---------------------------+
 * | length: int32  | type: int8 | body: UTF-8 bytes         |
 * +----------------+-----------+---------------------------+
 *   length = 1 + number of body bytes (it counts the type byte, not itself)
 * </pre>
 */
public record PaymentMessage(int type, String body) {
    public static final int AUTHORIZE = 1;
    public static final int CAPTURE = 2;
    public static final int APPROVED = 10;
}
