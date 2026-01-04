# Apache Deployment Notes

## Required Apache Modules

For Socket.io WebSocket support, ensure these modules are enabled:

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod rewrite
sudo a2enmod ssl  # For HTTPS
sudo systemctl restart apache2
```

## After Updating Apache Configs

1. Test configuration:
   ```bash
   sudo apache2ctl configtest
   ```

2. Reload Apache:
   ```bash
   sudo systemctl reload apache2
   ```

3. Check logs if issues persist:
   ```bash
   sudo tail -f /var/log/apache2/veilforce-error.log
   ```

## Memory Optimization

The SocketContext has been optimized to prevent memory leaks:
- Uses `useRef` to track socket instance
- Proper cleanup on unmount
- Reconnection limits to prevent infinite loops
- Removed circular dependencies in useEffect

## Troubleshooting Socket.io

If Socket.io still doesn't work:
1. Check Apache error logs
2. Verify WebSocket modules are enabled
3. Test direct connection: `curl http://localhost:5016/socket.io/`
4. Check browser console for WebSocket upgrade errors

