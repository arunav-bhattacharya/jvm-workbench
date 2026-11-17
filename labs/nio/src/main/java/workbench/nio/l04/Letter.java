package workbench.nio.l04;

/**
 * One letter on the post office's link. Wire format, big-endian:
 * <pre>
 * +----------------+-----------+---------------------------+
 * | length: int32  | type: int8 | body: UTF-8 bytes         |
 * +----------------+-----------+---------------------------+
 *   length = 1 + number of body bytes (it counts the type byte, not itself)
 * </pre>
 */
public record Letter(int type, String body) {
    public static final int NOTE = 1;
    public static final int PARCEL = 2;
    public static final int RECEIPT = 10;
}
