#################################################
Angularチュートリアル
#################################################
Last Updated on 2021-04-17

.. |date| date::

.. tip:: 本ページは、`ツアー・オフ・ヒーローズ <https://angular.jp/tutorial>`_ に沿って体験したときのメモです。詳細は本家参照願います。

新規プロジェクトの作成
============================================
新規アプリ生成
--------------------------------------------

ng new で実行::

  ng new angular-tour-of-heroes

アプリのサーブ
--------------------------------------------

ワークスペースに移動し、アプリケーションを起動::

  cd angular-tour-of-heroes
  ng serve --open

.. note:: --openフラグにより、http://localhost:4200が自動で開く。ここまでは入門編でも体験済み

アプリタイトルの変更
--------------------------------------------

app.component.ts (class title property)::

  title = 'Tour of Heroes';

.. code-block:: TypeScript
  :caption: app.component.ts (class title property)
  :linenos:
  :emphasize-lines: 9
  
  import { Component } from '@angular/core';

  @Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.css']
  })
  export class AppComponent {
    title = 'Tour of Heroes'; // ここを変更してみる
  }

.. code-block:: html
  :caption: app.component.html (template)
  :linenos:
  
  // 全部消して以下一行に編集
  <h1>{{title}}</h1>

こんな感じで表示が変わる

.. figure:: /ex/angular/change-title.png

.. tip:: {{変数名}} でバインディングの構文となっている。tsファイルのtitleをHTMLの{{title}}に渡すことで表示される。


アプリスタイルの変更
--------------------------------------------
チュートリアルに従って、src/style.cssを修正

.. code-block:: css
  :caption: src/styles.css (excerpt)
  :linenos:
  
  /* Application-wide Styles */
  h1 {
    color: #369;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 250%;
  }
  h2,
  h3 {
    color: #444;
    font-family: Arial, Helvetica, sans-serif;
    font-weight: lighter;
  }
  body {
    margin: 2em;
  }
  body,
  input[type="text"],
  button {
    color: #333;
    font-family: Cambria, Gergia;
  }
  /* everywhere else */
  * {
    font-family: Arial, Helvetica, sans-serif;
  }

文字の雰囲気が変わってればOK。こんな感じ。

.. figure:: /ex/angular/change-css.png

ヒーロー表示
============================================
heroesコンポーネント作成
--------------------------------------------

新規コンポーネント作成::

  $ ng generate component heroes
  CREATE src/app/heroes/heroes.component.html (21 bytes)
  CREATE src/app/heroes/heroes.component.spec.ts (626 bytes)
  CREATE src/app/heroes/heroes.component.ts (275 bytes)
  CREATE src/app/heroes/heroes.component.css (0 bytes)
  UPDATE src/app/app.module.ts (396 bytes)

.. figure:: /ex/angular/generate-component-heroes.png

HeroesComponentビューの表示
--------------------------------------------

.. code-block:: typescript
  :caption: app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 4-6, 9

  import { Component, OnInit } from '@angular/core';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    hero = 'Windstorm'; // 追加
    constructor() { }
    ngOnInit(): void {
    }

  }

.. tip:: 

  :selector: コンポーネントのCSS要素セレクター＝識別するHTML要素
  :templateUrl: コンポーネントのテンプレートファイルの場所
  :styleUrls: コンポーネントのプライベートCSSスタイルの場所

.. code-block:: html
  :caption: heroes.component.html
  :linenos:
  
  {{hero}}


.. code-block:: html
  :caption: src/app/app.component.html
  :linenos:
  :emphasize-lines: 2
  
  <h1>{{title}}</h1>
  <app-heroes></app-heroes>

ここまで対応すると、下記のように「Windstorm」が画面に表示されます。

.. figure:: /ex/angular/view-Windstorm.png


Heroインターフェースの作成
--------------------------------------------
ヒーローとして表示したいのは名前だけではない。インターフェースを作って表示する。

.. code-block:: typescript
  :caption: src/app/hero.ts(新規）
  :linenos:
  
  export interface Hero {
    id: number;
    name: string;
  }

.. code-block:: typescript
  :caption: app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 2, 10-13

  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  
  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    hero: Hero = {
      id: 1,
      name: 'Windstorm'
    };
    constructor() { }
    ngOnInit(): void {
    }

  }

.. code-block:: html
  :caption: app.component.html (template)
  :linenos:
  
  <h2>{{hero.name}} Details</h2>
  <div><span>id: </span>{{hero.id}}</div>
  <div><span>name: </span>{{hero.name}}</div>

表示はこんな感じ。

.. figure:: /ex/angular/view-id-Windstorm.png

UppercasePipeでの書式設定
--------------------------------------------

hero.nameのバインディングを修正::
  
  <h2>{{hero.name | uppercase}} Details</h2>

.. figure:: /ex/angular/view-id-Windstorm-upper.png

   

ヒーローの編集
--------------------------------------------
双方向バインディングできるように修正する。


.. code-block:: ng2
  :caption: app.component.html (template)
  :linenos:
  
  <h2>{{hero.name | uppercase}} Details</h2>
  <div><span>id: </span>{{hero.id}}</div>
  <div>
    <label>name:
      <input [(ngModel)]="hero.name" placeholder="name"/>
    </label>
  </div>

.. figure:: /ex/angular/ngModel.png


AppModule
--------------------------------------------
この状態では、以下のエラーが発生

.. figure:: /ex/angular/serve-error.png

.. tip:: [(ngModel)]が双方向バインディング構文。ngModelは有効なAngularディレクティブですが、デフォルトでは使用不可。FormsModuleモジュールをimportする必要あり。

.. code-block:: typescript
  :caption: src/app/app.module.ts
  :linenos:
  :emphasize-lines: 3,6,12,16
  
  import { BrowserModule } from '@angular/platform-browser';
  import { NgModule } from '@angular/core';
  import { FormsModule } from '@angular/forms'; // 追加

  import { AppComponent } from './app.component';
  import { HeroesComponent } from './heroes/heroes.component'; // 自動で追加されてた


  @NgModule({
    declarations: [
      AppComponent,
      HeroesComponent
    ],
    imports: [
      BrowserModule,
      FormsModule
    ],
    providers: [],
    bootstrap: [AppComponent]
  })
  export class AppModule { }

.. tip:: moduleは、app.module.tsで一元管理。HeroesComponent は、generateの際に自動で追加された。

moduleを整備すれば、エラーは消えて動作するようになる。formを修正するとh2タグも同期して編集される。

.. figure:: /ex/angular/ngModel-fix.png

   

リスト
============================================
モック作成
--------------------------------------------

.. code-block:: typescript
  :caption: src/app/mock-heroes.ts
  :linenos:
  
  import { Hero } from './hero'

  export const HEROES: Hero[] = [
    { id: 11, name: 'Dr Nice' },
    { id: 12, name: 'Narco' },
    { id: 13, name: 'Bombasto' },
    { id: 14, name: 'Celeritas' },
    { id: 15, name: 'Magneta' },
    { id: 16, name: 'RubberMan' },
    { id: 17, name: 'Dynama' },
    { id: 18, name: 'Dr IQ' },
    { id: 19, name: 'Magma' },
    { id: 20, name: 'Tornado' }
  ];

ngForで表示
--------------------------------------------

.. code-block:: typescript
  :caption: app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 2, 10

  import { Component, OnInit } from '@angular/core';
  import { HEROES } from '../mock-heroes';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes = HEROES;

    constructor() { }

    ngOnInit(): void {
    }

  }

.. code-block:: ng2
  :caption: app.component.html (template)
  :linenos:
  :emphasize-lines: 3
  
  <h2>My Heroes</h2>
  <ul class="heroes">
    <li *ngFor="let hero of heroes">
      <span class="badge">{{hero.id}}</span> {{hero.name}}
    </li>
  </ul>

.. tip::

  * ngForは、繰返しディレクティブ（ngForの前のアスタリスク(*)を忘れないように）
  * <li> を繰り返す
  * heroes（複数形） は HeroesComponentのリスト
  * hero（単数形） はループごとのオブジェクト

表示はこんな感じ。

.. figure:: /ex/angular/Mock-lists.png


hero個別のCSS整備
--------------------------------------------

.. code-block:: css
  :caption: src/app/heroes/heroes.component.css
  :linenos:
  :emphasize-lines: 8,18

  /* HeroesComponent's private CSS styles */
  .heroes {
    margin: 0 0 2em 0;
    list-style-type: none;
    padding: 0;
    width: 15em;
  }
  .heroes li {
    cursor: pointer;
    position: relative;
    left: 0;
    background-color: #EEE;
    margin: .5em;
    padding: .3em 0;
    height: 1.6em;
    border-radius: 4px;
  }
  .heroes li:hover {
    color: #607D8B;
    background-color: #DDD;
    left: .1em;
  }
  .heroes li.selected {
    background-color: #CFD8DC;
    color: white;
  }
  .heroes li.selected:hover {
    background-color: #BBD8DC;
    color: white;
  }
  .heroes .badge {
    display: inline-block;
    font-size: small;
    color: white;
    padding: 0.8em 0.7em 0 0.7em;
    background-color:#405061;
    line-height: 1em;
    position: relative;
    left: -1px;
    top: -4px;
    height: 1.8em;
    margin-right: .8em;
    border-radius: 4px 0 0 4px;
  }

.. figure:: /ex/angular/Mock-lists-css.png


クリックイベント
--------------------------------------------

クリックイベントのバインディング追加::

  <li *ngFor="let hero of heroes" (click)="onSelect(hero)">

componentを修正

.. code-block:: typescript
  :caption: app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 12, 19-21

  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HEROES } from '../mock-heroes';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes = HEROES;
    selectedHero: Hero;

    constructor() { }

    ngOnInit(): void {
    }

    onSelect(hero: Hero): void{
      this.selectedHero = hero;
    }
  }


ngIfで分岐を追加
--------------------------------------------
この時点で、ブラウザコンソールで以下のようなエラーが出てるはず。

.. figure:: /ex/angular/selectedHero-undefined.png


.. code-block:: ng2
  :caption: src/app/heroes/heroes.component.html (*ngIf)
  :linenos:
  :emphasize-lines: 10

  <h2>My Heroes</h2>
  <ul class="heroes">
    <li *ngFor="let hero of heroes"
      [class.selected]="hero === selectedHero"
      (click)="onSelect(hero)">
      <span class="badge">{{hero.id}}</span> {{hero.name}}
    </li>
  </ul>

  <div *ngIf="selectedHero">
  
    <h2>{{selectedHero.name | uppercase}} Details</h2>
    <div><span>id: </span>{{selectedHero.id}}</div>
    <div>
      <label>name:
        <input [(ngModel)]="selectedHero.name" placeholder="name"/>
      </label>
    </div>

  </div>


これで、初期状態でformがなく、選択するとformが表示されるようになる。

.. figure:: /ex/angular/if-selected.png

コンポーネント
============================================

ここでは、下記のdetail部分をコンポーネント化するのが目標です。

.. code-block:: ng2
  :caption: src/app/heroes/heroes.component.html
  :linenos:
  :emphasize-lines: 10-

  <h2>My Heroes</h2>
  <ul class="heroes">
    <li *ngFor="let hero of heroes"
      [class.selected]="hero === selectedHero"
      (click)="onSelect(hero)">
      <span class="badge">{{hero.id}}</span> {{hero.name}}
    </li>
  </ul>

  <!-- ここを外に出したい -->
  <div *ngIf="selectedHero">

    <h2>{{selectedHero.name | uppercase}} Details</h2>
    <div><span>id: </span>{{selectedHero.id}}</div>
    <div>
      <label>name:
        <input [(ngModel)]="selectedHero.name" placeholder="name"/>
      </label>
    </div>

  </div>

HeroDetailComponentの作成
--------------------------------------------
以下のコマンドで新規コンポーネントを作成::

  $ ng generate component hero-detail
  CREATE src/app/hero-detail/hero-detail.component.html (26 bytes)
  CREATE src/app/hero-detail/hero-detail.component.spec.ts (655 bytes)
  CREATE src/app/hero-detail/hero-detail.component.ts (294 bytes)
  CREATE src/app/hero-detail/hero-detail.component.css (0 bytes)
  UPDATE src/app/app.module.ts (601 bytes)

.. tip:: src/app/app.module.ts には自動でhero-detailの記述が追加されます。


templateの記述
--------------------------------------------
htmlテンプレートに、外だししたい部分を書き出しておきます。

.. code-block:: ng2
  :caption: src/app/hero-detail/hero-detail.component.html
  :linenos:

  <div *ngIf="selectedHero">

    <h2>{{selectedHero.name | uppercase}} Details</h2>
    <div><span>id: </span>{{selectedHero.id}}</div>
    <div>
      <label>name:
        <input [(ngModel)]="selectedHero.name" placeholder="name"/>
      </label>
    </div>

  </div>

この作業で以下のエラーが出ます。

.. figure:: /ex/angular/detail-error.png

次に、typescriptを修正します。

.. code-block:: typescript
  :caption: src/app/hero-detail/hero-detail.component.ts
  :linenos:
  :emphasize-lines: 1,2,10
  
  import { Component, OnInit, Input } from '@angular/core';
  import { Hero } from '../hero'

  @Component({
    selector: 'app-hero-detail',
    templateUrl: './hero-detail.component.html',
    styleUrls: ['./hero-detail.component.css']
  })
  export class HeroDetailComponent implements OnInit {
    @Input() hero: Hero;

    constructor() { }

    ngOnInit(): void {
    }

  }

.. hint:: 

  * Inputを用意し、別のコンポーネントからバインドされることを待ち構えます。
  * Inputの詳細 → `@Input() と @Output() プロパティ <https://angular.jp/guide/inputs-outputs>`_ 


親テンプレートの修正(コンポーネント化)
--------------------------------------------
.. code-block:: ng2
  :caption: src/app/heroes/heroes.component.html
  :linenos:
  :emphasize-lines: 10-

  <h2>My Heroes</h2>
  <ul class="heroes">
    <li *ngFor="let hero of heroes"
      [class.selected]="hero === selectedHero"
      (click)="onSelect(hero)">
      <span class="badge">{{hero.id}}</span> {{hero.name}}
    </li>
  </ul>

  <app-hero-detail [hero]="selectedHero"></app-hero-detail>

特に問題なければ、以下のような感じになってるはず。

.. figure:: /ex/angular/hero-detail.png

サービス
============================================
サービスの役割
--------------------------------------------

ここまで、データの部分をモックで記述していた部分をどうにかしていきます。データをどうやって取得するかという関心を外だしすること。そこでサービスという仕組みを使います。

.. code-block:: typescript
  :caption: src/app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 3
  
  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HEROES } from '../mock-heroes';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes = HEROES;
    selectedHero: Hero;

    constructor() { }

    ngOnInit(): void {
    }

    onSelect(hero: Hero): void{
      this.selectedHero = hero;
    }
  }

サービスの作成
--------------------------------------------

下記コマンドにて作成::

  $ ng generate service hero
  CREATE src/app/hero.service.spec.ts (347 bytes)
  CREATE src/app/hero.service.ts (133 bytes)

2ファイルできます。hero.service.tsに修正を入れていきますが、初版は下記状態です。

.. code-block:: typescript
  :caption: src/app/hero.service.ts
  :linenos:
  
  import { Injectable } from '@angular/core';

  @Injectable({
    providedIn: 'root'
  })
  export class HeroService {

    constructor() { }
  }

サービスにモックを移動
--------------------------------------------

.. code-block:: typescript
  :caption: src/app/hero.service.ts
  :linenos:
  :emphasize-lines: 2,3,12-14
  
  import { Injectable } from '@angular/core';
  import { Hero } from './hero';
  import { HEROES } from './mock-heroes';

  @Injectable({
    providedIn: 'root'
  })
  export class HeroService {

    constructor() { }

    getHeroes(): Hero[] {
      return HEROES;
    }

  }

.. code-block:: typescript
  :caption: src/app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 3,11,14,24-26
  
  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HeroService } from '../hero.service';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes: Hero[];
    selectedHero: Hero;

    constructor(private heroService: HeroService) { }

    ngOnInit(): void {
      this.getHeroes();
    }

    onSelect(hero: Hero): void{
      this.selectedHero = hero;
    }

    getHeroes(): void {
      this.heroes = this.heroService.getHeroes();
    }
  }

Observableデータ
--------------------------------------------
src/app/heroes/heroes.component.ts::

  this.heroes = this.heroService.getHeroes();

この部分を非同期実装する

.. code-block:: typescript
  :caption: src/app/hero.service.ts
  :linenos:
  :emphasize-lines: 2,12-13
  
  import { Injectable } from '@angular/core';
  import { Observable, of } from 'rxjs';
  import { Hero } from './hero';
  import { HEROES } from './mock-heroes';

  @Injectable({
    providedIn: 'root'
  })
  export class HeroService {
    constructor() { }

    getHeroes(): Observable<Hero[]> {
      return of(HEROES);
    }

  }


.. code-block:: typescript
  :caption: src/app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 25-26
  
  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HeroService } from '../hero.service';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes: Hero[];
    selectedHero: Hero;

    constructor(private heroService: HeroService) { }

    ngOnInit(): void {
      this.getHeroes();
    }

    onSelect(hero: Hero): void{
      this.selectedHero = hero;
    }

    getHeroes(): void {
      this.heroService.getHeroes()
        .subscribe(heroes => this.heroes = heroes);
    }
  }

.. hint:: プロパティへの代入から、subscripbeによるコールバックに変更


メッセージ表示
--------------------------------------------

メッセージコンポーネント追加::

  $ ng generate component messages
  CREATE src/app/messages/messages.component.html (23 bytes)
  CREATE src/app/messages/messages.component.spec.ts (640 bytes)
  CREATE src/app/messages/messages.component.ts (283 bytes)
  CREATE src/app/messages/messages.component.css (0 bytes)
  UPDATE src/app/app.module.ts (691 bytes)

メッセージサービス追加::

  $ ng generate service message
  CREATE src/app/message.service.spec.ts (362 bytes)
  CREATE src/app/message.service.ts (136 bytes)

追加したメッセージコンポーネントを表示するための修正

.. code-block:: html
  :caption: src/app/app.component.html
  :linenos:
  :emphasize-lines: 3
  
  <h1>{{title}}</h1>
  <app-heroes></app-heroes>
  <app-messages></app-messages>

メッセージサービスは、コンストラクタは削除して下記のように修正。

.. code-block:: typescript
  :caption: src/app/message.service.ts
  :linenos:
  :emphasize-lines: 7-15
  
  import { Injectable } from '@angular/core';

  @Injectable({
    providedIn: 'root',
  })
  export class MessageService {
    messages: string[] = [];

    add(message: string) {
      this.messages.push(message);
    }

    clear() {
      this.messages = [];
    }
  }

このサービスと連携できるようにしていく。まずは、hero.serviceとの連携

.. code-block:: typescript
  :caption: src/app/hero.service.ts
  :linenos:
  :emphasize-lines: 5,11,14
  
  import { Injectable } from '@angular/core';
  import { Observable, of } from 'rxjs';
  import { Hero } from './hero';
  import { HEROES } from './mock-heroes';
  import { MessageService } from './message.service';

  @Injectable({
    providedIn: 'root'
  })
  export class HeroService {
    constructor(private messageService: MessageService) { }

    getHeroes(): Observable<Hero[]> {
      this.messageService.add('HeroService: fetched heroes');
      return of(HEROES);
    }

  }

追加したメッセージコンポーネントも修正する。

.. code-block:: typescript
  :caption: src/app/messages/messages.component.ts
  :linenos:
  :emphasize-lines: 2,11
  
  import { Component, OnInit } from '@angular/core';
  import { MessageService } from '../message.service';

  @Component({
    selector: 'app-messages',
    templateUrl: './messages.component.html',
    styleUrls: ['./messages.component.css']
  })
  export class MessagesComponent implements OnInit {

    constructor(public messageService: MessageService) { }

    ngOnInit(): void {
    }

  }

これでサービスの変数をコンポーネント経由でバインドできる。

.. code-block:: ng2
  :caption: src/app/messages/messages.component.html
  :linenos:
  
  <div *ngIf="messageService.messages.length">
    <h2>Messages</h2>
    <button class="clear" (click)="messageService.clear()">clear</button>
    <div *ngFor='let message of messageService.messages'>{{message}}</div>
  </div>

これをメインの画面から表示されるように組み込んでいく。

.. code-block:: typescript
  :caption: src/app/heroes/heroes.component.ts
  :linenos:
  :emphasize-lines: 4,16,24
  
  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HeroService } from '../hero.service';
  import { MessageService} from '../message.service';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    selectedHero: Hero;

    heroes: Hero[];

    constructor(private heroService: HeroService, private messageService:MessageService) { }

    ngOnInit(): void {
      this.getHeroes();
    }

    onSelect(hero: Hero): void{
      this.selectedHero = hero;
      this.messageService.add(`HeroesComponent: Selected hero id=${hero.id}`)
    }

    getHeroes(): void {
      this.heroService.getHeroes()
        .subscribe(heroes => this.heroes = heroes);
    }
  }


こうなる。Heroを選択する都度、下のメッセージが表示される。

.. figure:: /ex/angular/add-message.png


ルーティング
============================================
AppRoutingModule追加
--------------------------------------------

ルーティング用のモジュールを追加します。::

  $ ng generate module app-routing --flat --module=app
  CREATE src/app/app-routing.module.ts (196 bytes)
  UPDATE src/app/app.module.ts (770 bytes)

.. tip:: 

  :--flat: 直下にファイルを作ってくれます。
  :--module=app: AppModuleへの自動追加

初期状態は下記。

.. code-block:: typescript
  :caption: src/app/app-routing.module.ts (generated)
  :linenos:
  
  import { NgModule } from '@angular/core';
  import { CommonModule } from '@angular/common';



  @NgModule({
    declarations: [],
    imports: [
      CommonModule
    ]
  })
  export class AppRoutingModule { }

これを以下のように書き換え

.. code-block:: typescript
  :caption: src/app/app-routing.module.ts (updated)
  :linenos:
  :emphasize-lines: 2-3,5-7,10-11
  
  import { NgModule } from '@angular/core';
  import { RouterModule, Routes } from '@angular/router';
  import { HeroesComponent } from './heroes/heroes.component';

  const routes = [
    { path: 'heroes', component: HeroesComponent }
  ];

  @NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule]
  })
  export class AppRoutingModule { }

.. tip:: 

  :path: ブラウザのアドレスバーにある URL にマッチする文字列
  :component: そのルートに遷移するときにルーターが作成すべきコンポーネント

  →　URLがlocalhost:4200/heroes　のようなアクセスが可能となる。

.. code-block:: html
  :caption: src/app/app.component.html 
  :linenos:
  :emphasize-lines: 2
  
  <h1>{{title}}</h1>
  <router-outlet></router-outlet>
  <app-messages></app-messages>

これでURLそのままのときタイトルだけになり、/heroesにアクセスすると一覧が表示されます。

.. figure:: /ex/angular/heroes-routing.png

rouerLink追加
--------------------------------------------
.. code-block:: html
  :caption: src/app/app.component.html 
  :linenos:
  :emphasize-lines: 2-4
  
  <h1>{{title}}</h1>
  <nav>
    <a routerLink="/heroes">Heroes</a>
  </nav>
  <router-outlet></router-outlet>
  <app-messages></app-messages>

.. figure:: /ex/angular/routerLink.png

.. hint:: routerLinkは、RouterLinkディレクティブのためのセレクター

ダッシュボード追加
--------------------------------------------

コンポーネントの追加::

  $ ng generate component dashboard
  CREATE src/app/dashboard/dashboard.component.html (24 bytes)
  CREATE src/app/dashboard/dashboard.component.spec.ts (647 bytes)
  CREATE src/app/dashboard/dashboard.component.ts (287 bytes)
  CREATE src/app/dashboard/dashboard.component.css (0 bytes)
  UPDATE src/app/app.module.ts (864 bytes)

以下の通り修正

.. code-block:: typescript
  :caption: src/app/dashboard/dashboard.component.ts
  :linenos:
  :emphasize-lines: 21
  
  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HeroService } from '../hero.service';

  @Component({
    selector: 'app-dashboard',
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.css']
  })
  export class DashboardComponent implements OnInit {
    heroes: Hero[] = [];

    constructor(private heroService: HeroService) { }

    ngOnInit(): void {
      this.getHeroes();
    }

    getHeroes(): void{
      this.heroService.getHeroes()
        .subscribe(heroes => this.heroes = heroes.slice(1,5));
    }

  }

.. hint:: 配列を1番目と5番目でスライスし、トップヒーローの4つを返すようにしている（2番目、3番目、4番目、5番目）

.. code-block:: ng2
  :caption: src/app/dashboard/dashboard.component.html
  :linenos:
  :emphasize-lines: 1
  
  <h3>Top Heroes</h3>
  <div class="grid grid-pad">
    <a *ngFor="let hero of heroes" class="col-1-4">
      <div class="module hero">
        <h4>{{hero.name}}</h4>
      </div>
    </a>
  </div>

.. code-block:: css
  :caption: src/app/dashboard/dashboard.component.css
  :linenos:
  
  /* DashboardComponent's private CSS styles */
  [class*='col-'] {
    float: left;
    padding-right: 20px;
    padding-bottom: 20px;
  }
  [class*='col-']:last-of-type {
    padding-right: 0;
  }
  a {
    text-decoration: none;
  }
  *, *:after, *:before {
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    box-sizing: border-box;
  }
  h3 {
    text-align: center;
    margin-bottom: 0;
  }
  h4 {
    position: relative;
  }
  .grid {
    margin: 0;
  }
  .col-1-4 {
    width: 25%;
  }
  .module {
    padding: 20px;
    text-align: center;
    color: #eee;
    max-height: 120px;
    min-width: 120px;
    background-color: #3f525c;
    border-radius: 2px;
  }
  .module:hover {
    background-color: #eee;
    cursor: pointer;
    color: #607d8b;
  }
  .grid-pad {
    padding: 10px 0;
  }
  .grid-pad > [class*='col-']:last-of-type {
    padding-right: 20px;
  }
  @media (max-width: 600px) {
    .module {
      font-size: 10px;
      max-height: 75px; }
  }
  @media (max-width: 1024px) {
    .grid {
      margin: 0;
    }
    .module {
      min-width: 60px;
    }
  }

.. code-block:: typescript
  :caption: src/app/app-routing.module.ts
  :linenos:
  :emphasize-lines: 4,7,8
  
  import { NgModule } from '@angular/core';
  import { RouterModule, Routes } from '@angular/router';
  import { HeroesComponent } from './heroes/heroes.component';
  import { DashboardComponent } from './dashboard/dashboard.component'

  const routes = [
    { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
    { path: 'dashboard', component: DashboardComponent},
    { path: 'heroes', component: HeroesComponent },
  ];

  @NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule]
  })
  export class AppRoutingModule { }

.. code-block:: html
  :caption: src/app/app-routing.module.ts
  :linenos:
  :emphasize-lines: 3
  
  <h1>{{title}}</h1>
  <nav>
    <a routerLink="/dashboard">Dashboard</a>
    <a routerLink="/heroes">Heroes</a>
  </nav>
  <router-outlet></router-outlet>
  <app-messages></app-messages>

ここまで対応すると以下のような画面。Dashboardと、Heroesのリンクが格好悪いのが気になる方は、チュートリアルから「src/app/app.component.css」を先に整備しておくとよいです。

.. figure:: /ex/angular/dashboard.png

HeroesComponentのクリーンアップ
--------------------------------------------
onSelect()メソッドとselectedHeroプロパティが使われなくなってるので掃除しておく。

.. code-block:: typescript
  :caption: src/app/heroes/heroes.component.ts
  :linenos:

  import { Component, OnInit } from '@angular/core';
  import { Hero } from '../hero';
  import { HeroService } from '../hero.service';

  @Component({
    selector: 'app-heroes',
    templateUrl: './heroes.component.html',
    styleUrls: ['./heroes.component.css']
  })
  export class HeroesComponent implements OnInit {
    heroes: Hero[];

    constructor(private heroService: HeroService) { }

    ngOnInit(): void {
      this.getHeroes();
    }

    getHeroes(): void {
      this.heroService.getHeroes()
        .subscribe(heroes => this.heroes = heroes);
    }
  }


HeroDetailComponentへのルート整備
--------------------------------------------
この部分はチュートリアルは言葉少ないが、多くのファイルでコード変更しないと動くところまでいかない。またここまでくるとファイルも増えており、どのコードを修正しているのかも混乱しがち。チュートリアルにある最終コードを見ながら対応した。

.. tip:: 

  * 引数のためのIDを、JavaScriptで、(+) 演算子は文字列を数値に変換する特性を使っている。
  * getHeroes（複数形） と　getHero（単数形）　を意識して対応する。

.. code-block:: typescript
  :caption: src/app/app-routing.module.ts
  :linenos:
  :emphasize-lines: 10
  
  import { NgModule } from '@angular/core';
  import { RouterModule, Routes } from '@angular/router';
  import { HeroesComponent } from './heroes/heroes.component';
  import { DashboardComponent } from './dashboard/dashboard.component';
  import { HeroDetailComponent } from './hero-detail/hero-detail.component';

  const routes = [
    { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
    { path: 'heroes', component: HeroesComponent },
    { path: 'detail/:id', component: HeroDetailComponent },
    { path: 'dashboard', component: DashboardComponent},
  ];

  @NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule]
  })
  export class AppRoutingModule { }

.. code-block:: typescript
  :caption: src/app/hero.service.ts
  :linenos:
  :emphasize-lines: 18-21
  
  import { Injectable } from '@angular/core';
  import { Observable, of } from 'rxjs';
  import { Hero } from './hero';
  import { HEROES } from './mock-heroes';
  import { MessageService } from './message.service';

  @Injectable({
    providedIn: 'root'
  })
  export class HeroService {
    constructor(private messageService: MessageService) { }

    getHeroes(): Observable<Hero[]> {
      this.messageService.add('HeroService: fetched heroes');
      return of(HEROES);
    }

    getHero(id: number): Observable<Hero> {
      this.messageService.add(`HeroService: fetched hero id=${id}`);
      return of(HEROES.find(hero => hero.id === id));
    }
  }

.. code-block:: ng2
  :caption: src/app/dashboard/dashboard.component.html
  :linenos:
  :emphasize-lines: 4
  
  <h3>Top Heroes</h3>
  <div class="grid grid-pad">
    <a *ngFor="let hero of heroes" class="col-1-4"
        routerLink="/detail/{{hero.id}}">
      <div class="module hero">
        <h4>{{hero.name}}</h4>
      </div>
    </a>
  </div>

.. code-block:: ng2
  :caption: src/app/heroes/heroes.component.html
  :linenos:
  :emphasize-lines: 4,6
  
  <h2>My Heroes</h2>
  <ul class="heroes">
    <li *ngFor="let hero of heroes">
      <a routerLink="/detail/{{hero.id}}">
        <span class="badge">{{hero.id}}</span> {{hero.name}}
      </a>
    </li>
  </ul>


サーバ通信
============================================
シミュレーションサーバ
--------------------------------------------
In-memory Web APIインストール::

  $ npm install angular-in-memory-web-api --save

  added 1 package, removed 1 package, and audited 1502 packages in 3s

  80 packages are looking for funding
    run `npm fund` for details

  found 0 vulnerabilities

HTTPサービス有効化
--------------------------------------------
HTTPクライアントと、シミュレーションサーバを有効化しておきます。

.. code-block:: typescript
  :caption: caption
  :linenos:
  :emphasize-lines: 4,6-7,23,28-29
  
  import { NgModule } from '@angular/core';
  import { BrowserModule } from '@angular/platform-browser';
  import { FormsModule } from '@angular/forms';
  import { HttpClientModule } from '@angular/common/http';

  import { HttpClientInMemoryWebApiModule } from 'angular-in-memory-web-api';
  import { InMemoryDataService } from './in-memory-data.service';

  import { AppRoutingModule } from './app-routing.module';

  import { AppComponent } from './app.component';
  import { DashboardComponent } from './dashboard/dashboard.component';
  import { HeroDetailComponent } from './hero-detail/hero-detail.component';
  import { HeroesComponent } from './heroes/heroes.component';
  import { HeroSearchComponent } from './hero-search/hero-search.component';
  import { MessagesComponent } from './messages/messages.component';

  @NgModule({
    imports: [
      BrowserModule,
      FormsModule,
      AppRoutingModule,
      HttpClientModule,

      // The HttpClientInMemoryWebApiModule module intercepts HTTP requests
      // and returns simulated server responses.
      // Remove it when a real server is ready to receive requests.
      HttpClientInMemoryWebApiModule.forRoot(
        InMemoryDataService, { dataEncapsulation: false }
      )
    ],
    declarations: [
      AppComponent,
      DashboardComponent,
      HeroesComponent,
      HeroDetailComponent,
      MessagesComponent,
      HeroSearchComponent
    ],
    bootstrap: [ AppComponent ]
  })
  export class AppModule { }

in-memory-dataサービスの作成
--------------------------------------------

サービス作成::

  $ ng generate service InMemoryData
  CREATE src/app/in-memory-data.service.spec.ts (389 bytes)
  CREATE src/app/in-memory-data.service.ts (141 bytes)

.. code-block:: typescript
  :caption: src/app/in-memory-data.service.ts
  :linenos:
  :emphasize-lines: 2-3,8-23,30-32
  
  import { Injectable } from '@angular/core';
  import { InMemoryDbService } from 'angular-in-memory-web-api';
  import { Hero } from './hero';

  @Injectable({
    providedIn: 'root',
  })
  export class InMemoryDataService implements InMemoryDbService {
    createDb() {
      const heroes = [
        { id: 11, name: 'Dr Nice' },
        { id: 12, name: 'Narco' },
        { id: 13, name: 'Bombasto' },
        { id: 14, name: 'Celeritas' },
        { id: 15, name: 'Magneta' },
        { id: 16, name: 'RubberMan' },
        { id: 17, name: 'Dynama' },
        { id: 18, name: 'Dr IQ' },
        { id: 19, name: 'Magma' },
        { id: 20, name: 'Tornado' }
      ];
      return {heroes};
    }

    // Overrides the genId method to ensure that a hero always has an id.
    // If the heroes array is empty,
    // the method below returns the initial number (11).
    // if the heroes array is not empty, the method below returns the highest
    // hero id + 1.
    genId(heroes: Hero[]): number {
      return heroes.length > 0 ? Math.max(...heroes.map(hero => hero.id)) + 1 : 11;
    }
  }


さて、ここでブラウザを更新すれば、表示されるはずなのですが、、、以下のようなメッセージが出て進まなくなりました::

  in-memory-data.service.ts is missing from the TypeScript compilation. Please make sure it is in your tsconfig via the 'files' or 'include' property.

メッセージから、 :kbd:`tsconfig` とやらをいじる必要があるようなのですが…これは、実はこれ、単にサーバを再起動すれば大丈夫。焦った。。。::

  ctr+C で中断
  ng serve --open

このチュートリアルでは、基本的なCRUD操作と、検索に関するチュートリアルが詰まっている。本メモではこの体験はせず、ここまで。
