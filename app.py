from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy

# Configurações
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teste1.db'

db = SQLAlchemy(app)


# Banco de dados
class Questao(db.Model):
    __tablename__ = 'questoes'
    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String, nullable=False, unique=True)
    alternativas = db.Column(db.String, nullable=False)
    gabarito = db.Column(db.String, nullable=False)

    def __init__(self, pergunta, alternativas, gabarito):
        self.pergunta = pergunta
        self.alternativas = alternativas
        self.gabarito = gabarito

    def get_pergunta(self):
        return self.pergunta

    def get_alternativas(self):
        # Dividir a string 'alternativas' usando ';' como delimitador e retornar a lista resultante
        lista_alternativas = self.alternativas.split(';')
        return lista_alternativas

    def get_gabarito(self):
        return self.gabarito


class Gerenciador:
    @staticmethod
    def criar_questao(pergunta, alternativas, gabarito):
        questao_existente = Questao.query.filter_by(pergunta=pergunta, gabarito=gabarito).first()
        if questao_existente:
            flash('Já existe uma questão igual a essa!', 'warning')
            return None

        nova_questao = Questao(pergunta, alternativas, gabarito)
        db.session.add(nova_questao)
        db.session.commit()

        flash('A questão foi criada com sucesso!', 'success')
        return nova_questao

    @staticmethod
    def excluir_questao(questao_id):
        questao = Questao.query.get(questao_id)
        if questao:
            db.session.delete(questao)
            db.session.commit()
            flash('Questão excluída com sucesso!', 'success')
        else:
            flash('Questão não encontrada!', 'danger')


# Rotas
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
def admin():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página!', 'warning')
        return render_template('admin.html')
    questoes = Questao.query.all()
    return render_template('admin.html', questoes=questoes)


@app.route('/admin/adicionar_pergunta', methods=['POST'])
def adicionar_pergunta():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página!', 'warning')
        return redirect(url_for('admin'))

    pergunta = request.form['pergunta']
    alternativas = request.form['alternativas']
    gabarito = request.form['gabarito']

    if not pergunta or not alternativas or not gabarito:
        flash('Algo deu errado!', 'warning')
        return redirect(url_for('admin'))

    Gerenciador.criar_questao(pergunta, alternativas, gabarito)

    return redirect(url_for('admin'))


@app.route('/admin/excluir_questao/<int:questao_id>')
def excluir_questao(questao_id):
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página!', 'warning')
        return redirect(url_for('admin'))

    Gerenciador.excluir_questao(questao_id)
    return redirect(url_for('admin'))


@app.route('/entrar', methods=['POST'])
def entrar():
    if request.form['nome'] == '123' and request.form['senha'] == '123':
        session['username'] = 'admin'
        return redirect(url_for('admin'))

    flash('Algo de errado!', 'warning')
    return redirect(url_for('admin'))


@app.route('/sair')
def sair():
    if 'username' not in session:
        flash('Você precisa estar logado para executar essa ação!', 'warning')
        return redirect(url_for('index'))
    session.pop('username', None)
    flash('Você desconectou com sucesso! Sentiremos sua falta por aqui...', 'success')
    return redirect(url_for('index'))


@app.route('/devs')
def devs():
    return render_template('devs.html')


@app.route('/quiz')
def quiz():
    session['score'] = 0
    session['question_index'] = 0
    session['answers'] = []
    return redirect(url_for('pergunta'))


@app.route('/pergunta', methods=['GET', 'POST'])
def pergunta():
    if request.method == 'POST':
        resposta = request.form['resposta']
        questao_id = request.form['questao_id']
        questao = Questao.query.get(questao_id)
        session['answers'].append((questao_id, resposta))
        if resposta == questao.get_gabarito():
            session['score'] += 1
        session['question_index'] += 1

    if session['question_index'] < 10:
        questao = Questao.query.offset(session['question_index']).first()
        if not questao:
            return redirect(url_for('resultado'))
        return render_template('pergunta.html', questao=questao)
    else:
        return redirect(url_for('resultado'))


@app.route('/resultado')
def resultado():
    score = session.get('score', 0)
    return render_template('resultado.html', score=score)


# Inicializar a base de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
