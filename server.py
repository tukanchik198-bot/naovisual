# by https://t.me/darkvibe
import os
import sys
import json
import uuid
import hashlib
import secrets
import datetime
import fnmatch
from functools import wraps

from flask import (
    Flask, request, Response, session, redirect, url_for,
    send_from_directory, abort, jsonify
)

from cryptography.fernet import Fernet

# by https://t.me/darkvibe
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
KEYS_FILE = os.path.join(DATA_DIR, 'keys.json')
SECRET_KEY_FILE = os.path.join(DATA_DIR, 'secret.key')
ADMINS_FILE = os.path.join(DATA_DIR, 'admins.json')

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_NAME'] = 'nao_session'

# by https://t.me/darkvibe
ROUTE_MAP = {
    '/': 'index.html',
    '/auth': 'auth.html',
    '/me': 'account.html',
    '/purchase': 'purchase.html',
    '/me/purchase': 'my-purchases.html',
    '/me/themes': 'themes.html',
    '/me/ecosystem': 'ecosystem.html',
    '/me/referral': 'referral.html',
    '/documents': 'documents.html',
}

ME_ROUTES = ['/me', '/me/purchase', '/me/themes', '/me/ecosystem', '/me/referral']


# by https://t.me/darkvibe
def init_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SECRET_KEY_FILE):
        key = Fernet.generate_key()
        with open(SECRET_KEY_FILE, 'wb') as f:
            f.write(key)
    if not os.path.exists(USERS_FILE):
        save_encrypted(USERS_FILE, {})
    if not os.path.exists(KEYS_FILE):
        save_encrypted(KEYS_FILE, {'keys': [], 'subscriptions': []})
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'admins': ['admin']}, f, ensure_ascii=False, indent=2)


# by https://t.me/darkvibe
def get_fernet():
    with open(SECRET_KEY_FILE, 'rb') as f:
        return Fernet(f.read())


def load_encrypted(filepath):
    fernet = get_fernet()
    with open(filepath, 'rb') as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode('utf-8'))


def save_encrypted(filepath, data):
    fernet = get_fernet()
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
    encrypted = fernet.encrypt(json_bytes)
    with open(filepath, 'wb') as f:
        f.write(encrypted)


# by https://t.me/darkvibe
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return h, salt


# by https://t.me/darkvibe
def get_users():
    try:
        return load_encrypted(USERS_FILE)
    except Exception:
        return {}


def save_users(users):
    save_encrypted(USERS_FILE, users)


def get_keys_data():
    try:
        return load_encrypted(KEYS_FILE)
    except Exception:
        return {'keys': [], 'subscriptions': []}


def save_keys_data(data):
    save_encrypted(KEYS_FILE, data)


# by https://t.me/darkvibe
def get_admins():
    try:
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('admins', [])
    except Exception:
        return ['admin']


def is_admin(username):
    return username in get_admins()


# by https://t.me/darkvibe
def create_default_admin():
    users = get_users()
    if 'admin' not in users:
        pw_hash, salt = hash_password('admin123')
        users['admin'] = {
            'username': 'admin',
            'email': 'admin@NaoVisuals.su',
            'password_hash': pw_hash,
            'salt': salt,
            'role': 'admin',
            'subscription_type': 'Premium',
            'subscription_end': None,
            'is_banned': False,
            'hwid': '',
            'created_at': datetime.datetime.now().isoformat()
        }
        save_users(users)
    admins = get_admins()
    if 'admin' not in admins:
        admins.append('admin')
        with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'admins': admins}, f, ensure_ascii=False, indent=2)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect('/auth')
        users = get_users()
        user = users.get(session['username'])
        if not user or user.get('is_banned'):
            session.clear()
            return redirect('/auth')
        return f(*args, **kwargs)
    return decorated


# by https://t.me/darkvibe
def find_html_files():
    files = []
    for f in os.listdir(BASE_DIR):
        if f.endswith('.html'):
            files.append(f)
    return files


def find_files_folder(html_filename):
    base = os.path.splitext(html_filename)[0]
    folder_name = base + '_files'
    folder_path = os.path.join(BASE_DIR, folder_name)
    if os.path.isdir(folder_path):
        return folder_name
    return None


def get_page_title(route):
    titles = {
        '/': 'NaoVisuals — Premium DLC',
        '/auth': 'Вход',
        '/me': 'Аккаунт',
        '/purchase': 'Покупка',
        '/me/purchase': 'Мои покупки',
        '/me/themes': 'Cloud Themes',
        '/me/ecosystem': 'Ecosystem',
        '/me/referral': 'Referral',
        '/documents': 'Документы',
    }
    return titles.get(route, 'NaoVisuals')


# by https://t.me/darkvibe
def get_nav_script(route):
    username = session.get('username', '')
    logged_in = bool(username)

    auth_block = ''
    if logged_in:
        auth_block = f'''
        <div id="__auth_panel" style="position:fixed;top:12px;right:16px;z-index:99999;display:flex;align-items:center;gap:10px;font-family:system-ui,sans-serif;">
            <a href="/me" style="color:#c4b5fd;text-decoration:none;font-size:13px;font-weight:600;background:rgba(124,58,237,.15);padding:6px 14px;border-radius:8px;border:1px solid rgba(124,58,237,.3);">{username}</a>
            <a href="/auth?logout=1" onclick="fetch('/auth?logout=1',{{method:'POST'}});return true;" style="color:#f87171;text-decoration:none;font-size:12px;opacity:.8;">Выйти</a>
        </div>'''
    else:
        auth_block = '''
        <div id="__auth_panel" style="position:fixed;top:12px;right:16px;z-index:99999;font-family:system-ui,sans-serif;">
            <a href="/auth" style="color:#c4b5fd;text-decoration:none;font-size:13px;font-weight:600;background:rgba(124,58,237,.15);padding:6px 14px;border-radius:8px;border:1px solid rgba(124,58,237,.3);">Войти</a>
        </div>'''

    return f'''
<script>
(function(){{
    var style = document.createElement('style');
    style.textContent = `
        body {{ padding-right: 0 !important; }}
        a[href*="t.me"], a[href*="purchase"], a[href*="subscribe"] {{ }}
    `;
    document.head.appendChild(style);

    document.body.insertAdjacentHTML('beforeend', `{auth_block}`);

    document.querySelectorAll('a[href="/purchase"], a[href*="subscribe"], a[href*="buy"], a[href*="t.me"]').forEach(function(btn) {{
        btn.addEventListener('click', function(e) {{
            e.preventDefault();
            e.stopPropagation();
            window.open('https://t.me/darkvibe', '_blank');
        }});
    }});

    var links = document.querySelectorAll('nav a, .sidebar a, [class*="nav"] a, [class*="menu"] a');
    links.forEach(function(link) {{
        var href = link.getAttribute('href');
        if (href === '{route}') {{
            link.style.color = '#c4b5fd';
            link.style.fontWeight = '700';
            link.style.background = 'rgba(124,58,237,.12)';
            link.style.borderRadius = '8px';
        }}
    }});

    var extra = document.createElement('style');
    extra.textContent = '.inline-block{{display:inline-block!important}}[style*="flex-wrap:wrap"]{{flex-direction:row!important}}[class*="split-"]{{display:inline!important;visibility:visible!important;opacity:1!important;transform:none!important;filter:none!important;position:relative!important}}';
    document.head.appendChild(extra);
}})();
</script>'''


# by https://t.me/darkvibe
def inject_into_html(html_content, route):
    nav_script = get_nav_script(route)
    base_tag = '<base href="/">'
    if '<head' in html_content:
        head_open = html_content.index('<head')
        head_close = html_content.index('>', head_open) + 1
        html_content = html_content[:head_close] + base_tag + html_content[head_close:]
    if '</head>' in html_content:
        html_content = html_content.replace('</head>', nav_script + '\n</head>', 1)
    elif '<body' in html_content:
        idx = html_content.index('<body')
        close = html_content.index('>', idx) + 1
        html_content = html_content[:close] + nav_script + html_content[close:]
    else:
        html_content = nav_script + html_content
    return html_content


def get_auth_page(error_msg='', error_display='none'):
    filepath = os.path.join(BASE_DIR, 'auth.html')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    err_script = ''
    if error_msg:
        err_script = f'<script>window.addEventListener("DOMContentLoaded",function(){{var e=document.getElementById("err");e.textContent={repr(error_msg)};e.style.display="block"}})</script>'
    content = content.replace('</head>', err_script + '\n</head>')
    return content


# by https://t.me/darkvibe
@app.route('/auth', methods=['GET', 'POST'])
def auth_page():
    if request.args.get('logout') == '1' or request.method == 'POST' and request.form.get('action') == 'logout':
        session.clear()
        return redirect('/auth')

    if request.method == 'POST':
        action = request.form.get('action', '')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if action == 'login':
            users = get_users()
            user = users.get(username)
            if user and not user.get('is_banned'):
                pw_hash, _ = hash_password(password, user['salt'])
                if pw_hash == user['password_hash']:
                    session['username'] = username
                    return redirect('/me')
            return Response(get_auth_page('Неверное имя пользователя или пароль', 'block'), mimetype='text/html; charset=utf-8')

        elif action == 'register':
            email = request.form.get('email', '').strip()
            if not username or not password or not email:
                return Response(get_auth_page('Заполните все поля', 'block'), mimetype='text/html; charset=utf-8')
            users = get_users()
            if username in users:
                return Response(get_auth_page('Пользователь уже существует', 'block'), mimetype='text/html; charset=utf-8')
            for u in users.values():
                if u.get('email') == email:
                    return Response(get_auth_page('Email уже используется', 'block'), mimetype='text/html; charset=utf-8')
            pw_hash, salt = hash_password(password)
            users[username] = {
                'username': username,
                'email': email,
                'password_hash': pw_hash,
                'salt': salt,
                'role': 'user',
                'subscription_type': None,
                'subscription_end': None,
                'is_banned': False,
                'hwid': '',
                'created_at': datetime.datetime.now().isoformat()
            }
            save_users(users)
            session['username'] = username
            return redirect('/me')

    return Response(get_auth_page('', 'none'), mimetype='text/html; charset=utf-8')


@app.route('/api/auth/check', methods=['GET'])
def api_auth_check():
    if 'username' in session:
        users = get_users()
        user = users.get(session['username'])
        if user and not user.get('is_banned'):
            return jsonify({'logged_in': True, 'username': session['username'], 'role': user.get('role', 'user')})
    return jsonify({'logged_in': False})


# by https://t.me/darkvibe
@app.route('/api/activate', methods=['POST'])
def api_activate():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    data = request.get_json()
    key = data.get('key', '').strip()
    keys_data = get_keys_data()
    for k in keys_data.get('keys', []):
        if k['key'] == key:
            if k.get('used_by') and k['used_by'] != session['username']:
                return jsonify({'success': False, 'message': 'Key already used'})
            exp = datetime.datetime.strptime(k['expires'], '%Y-%m-%d %H:%M:%S')
            if datetime.datetime.now() > exp:
                return jsonify({'success': False, 'message': 'Key expired'})
            users = get_users()
            user = users.get(session['username'])
            if user:
                user['subscription_type'] = k['type']
                user['subscription_end'] = k['expires']
                k['used_by'] = session['username']
                save_users(users)
                save_keys_data(keys_data)
                return jsonify({'success': True, 'message': f'Activated {k["type"]} subscription'})
    return jsonify({'success': False, 'message': 'Invalid key'})


@app.route('/')
def index():
    return serve_protected_page('/')


@app.route('/me')
@login_required
def account_page():
    return serve_protected_page('/me')


@app.route('/me/purchase')
@login_required
def my_purchases():
    return serve_protected_page('/me/purchase')


@app.route('/me/themes')
@login_required
def themes_page():
    return serve_protected_page('/me/themes')


@app.route('/me/ecosystem')
@login_required
def ecosystem_page():
    return serve_protected_page('/me/ecosystem')


@app.route('/me/referral')
@login_required
def referral_page():
    return serve_protected_page('/me/referral')


@app.route('/purchase')
def purchase_page():
    return serve_protected_page('/purchase')


@app.route('/documents')
def documents_page():
    return serve_protected_page('/documents')


# by https://t.me/darkvibe
def serve_protected_page(route):
    html_file = ROUTE_MAP.get(route)
    if not html_file:
        abort(404)
    filepath = os.path.join(BASE_DIR, html_file)
    if not os.path.isfile(filepath):
        abort(404)
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    username = session.get('username', '')
    email = ''
    sub_type = ''
    sub_end = ''
    uid = ''
    if username:
        users = get_users()
        user = users.get(username, {})
        email = user.get('email', '')
        sub_type = user.get('subscription_type') or ''
        sub_end = user.get('subscription_end') or ''
        uid = 'UID' + str(abs(hash(username)) % 100000)
    content = content.replace('{{__USERNAME__}}', username)
    content = content.replace('{{__EMAIL__}}', email)
    content = content.replace('{{__SUB_TYPE__}}', sub_type)
    content = content.replace('{{__SUB_END__}}', sub_end)
    content = content.replace('{{__UID__}}', uid)
    if sub_type:
        content = content.replace('{{__SUB_DISPLAY__}}', sub_type)
        content = content.replace('{{__SUB_END_DISPLAY__}}', sub_end or 'Бессрочно')
    else:
        content = content.replace('{{__SUB_DISPLAY__}}', 'Нет подписки')
        content = content.replace('{{__SUB_END_DISPLAY__}}', '—')
    content = inject_into_html(content, route)
    return Response(content, mimetype='text/html; charset=utf-8')


# by https://t.me/darkvibe
@app.route('/<path:filepath>')
def serve_static(filepath):
    decoded = filepath

    full_path = os.path.join(BASE_DIR, decoded)
    full_path = os.path.normpath(full_path)

    if not full_path.startswith(BASE_DIR):
        abort(403)

    if os.path.isfile(full_path):
        return send_file_safe(full_path)

    if os.path.isdir(full_path):
        for name in os.listdir(full_path):
            if name.endswith('.html'):
                return send_file_safe(os.path.join(full_path, name))

    html_files = find_html_files()
    for hf in html_files:
        base = os.path.splitext(hf)[0]
        folder = base + '_files'
        if decoded.startswith(folder + '/'):
            rel = decoded[len(folder) + 1:]
            file_path = os.path.join(BASE_DIR, folder, rel)
            file_path = os.path.normpath(file_path)
            if file_path.startswith(BASE_DIR) and os.path.isfile(file_path):
                return send_file_safe(file_path)

    return send_file_safe(full_path)


# by https://t.me/darkvibe
def send_file_safe(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mime_types = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.webp': 'image/webp',
        '.mp4': 'video/mp4',
    }
    mime = mime_types.get(ext, 'application/octet-stream')
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        resp = Response(content, mimetype=mime)
        resp.headers['Cache-Control'] = 'public, max-age=3600'
        return resp
    except Exception:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return '''
    <!DOCTYPE html><html><head><title>404</title>
    <style>body{background:#101012;color:#e2e8f0;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center}
    h1{font-size:72px;color:#7c3aed;margin-bottom:8px}p{color:#71717a}a{color:#c4b5fd;text-decoration:none}</style>
    </head><body><div><h1>404</h1><p>Page not found</p><br><a href="/">Back to home</a></div></body></html>
    ''', 404


# by https://t.me/darkvibe
def _bootstrap():
    init_data()
    create_default_admin()


_bootstrap()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    print(f'\n  NaoVisuals Server running on http://0.0.0.0:{port}\n')
    print('  Routes:')
    for route, fname in sorted(ROUTE_MAP.items()):
        print(f'    http://localhost:{port}{route:<20s} -> {fname}')
    print(f'\n  Default admin: admin / admin123\n')

    app.run(host='0.0.0.0', port=port, debug=False)
