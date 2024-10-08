
package org.openhab.binding.mideaac.internal.discovery;

import java.io.Closeable;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;

import org.eclipse.jdt.annotation.NonNullByDefault;


@NonNullByDefault
public class Connection implements Closeable {

    /**
     * UDP port to send command.
     */
    public static final int MIDEAAC_SEND_PORT1 = 6445;
    public static final int MIDEAAC_SEND_PORT2 = 20086;
    /**
     * UDP port devices send discover replies back.
     */
    public static final int MIDEAAC_RECEIVE_PORT = 6440;

    private final InetAddress iNetAddress;
    private final DatagramSocket socket;

    /**
     * Initializes a connection to the given IP address.
     *
     * @param ipAddress IP address of the connection
     * @throws UnknownHostException if ipAddress could not be resolved.
     * @throws SocketException if no Datagram socket connection could be made.
     */
    public Connection(String ipAddress) throws SocketException, UnknownHostException {
        iNetAddress = InetAddress.getByName(ipAddress);
        socket = new DatagramSocket();
    }

    /**
     * Sends the 9 bytes command to the Midea AC device.
     *
     * @param command the 9 bytes command
     * @throws IOException Connection to the bulb failed
     */
    public void sendCommand(byte[] command) throws IOException {
        {
            DatagramPacket sendPkt = new DatagramPacket(command, command.length, iNetAddress, MIDEAAC_SEND_PORT1);
            socket.send(sendPkt);
        }
        {
            DatagramPacket sendPkt = new DatagramPacket(command, command.length, iNetAddress, MIDEAAC_SEND_PORT2);
            socket.send(sendPkt);
        }

    }

    @Override
    public void close() {
        socket.close();
    }
}